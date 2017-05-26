import csv
import os
import time

import re
from pprint import pprint

from selenium import webdriver
from browsermobproxy import Server
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from slugify import slugify

py_location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
src_path = os.path.join(py_location, 'src')
CHROMEDRIVER_PATH = os.path.join(src_path, 'chromedriver')
BROWSERMOBPROXY_PATH = os.path.join(src_path, 'browsermob-proxy-2.1.4/bin/browsermob-proxy')
PAUSE_TIME = 0.5
# os.environ.setdefault('https_proxy', 'https://212.237.36.33:8080')


class Parser():
    def __init__(self, url, user, password, folder: str = ''):
        self.rows = {}
        self.folder = folder or py_location
        self._user = user
        self._password = password
        self.url = url
        self.mp3_url_pattern = re.compile("mp3\?extra=")
        self.audio_name_pattern = re.compile(
            r'(?<=class="audio_title_inner" tabindex="0" nodrag="1" aria-label=")[^"]*')
        self.audio_performer_pattern = re.compile(r'(?<=class="audio_performer">)[^<]*')
        self.audio_pattern = re.compile(r'(audio_-\d*_\d*)')
        self.filename_pattern = re.compile(r'(?<=audios)-\d*')
        self.filename_playlist_pattern = re.compile(r'(?<=audio)_playlist-\d*_?\d*')
        self.fieldnames = ['name', 'performer', 'url', 'audio_tag']
        self.browser_pause_time = PAUSE_TIME
        self.used_urls = set()
        self.used_audios = set()
        self.all_requests = []

        try:
            audios_number = self.filename_pattern.search(self.url).group()
        except AttributeError:
            audios_number = self.filename_playlist_pattern.search(self.url).group()
        csv_filename = 'audios_list_{}.csv'.format(audios_number)
        self.spreadsheet_filename = os.path.join(self.folder, csv_filename)
        self.proxy = None
        self.browser = None
        self.setup_selenium()

    def setup_selenium(self):
        server = Server(BROWSERMOBPROXY_PATH)
        server.start()
        self.proxy = server.create_proxy({'captureHeaders': True, 'captureContent': True, 'captureBinaryContent': True})
        service_args = ["--proxy=%s" % self.proxy.proxy, '--ignore-ssl-errors=yes']
        chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument("--proxy-server={}".format('212.237.36.33:8080'))
        chrome_options.add_argument("--proxy-server={}".format(self.proxy.proxy))
        self.browser = webdriver.Chrome(CHROMEDRIVER_PATH, service_args=service_args, chrome_options=chrome_options)
        self.proxy.new_har()

    def create_csv_for_download(self):
        if os.path.exists(self.spreadsheet_filename):
            pass
            # print('Spreadsheet with urls seems to exist in the folder...')
        else:
            self.browser.get(self.url)

            self.login()

            self.scroll_down()
            self.scroll_top()

            self.parse_audio_names()
            self.load_existing_records()
            self.take_audios()


            print('Spreadsheet with music urls created successfully.')

    def login(self):
        username = self.browser.find_element_by_id("email")
        password = self.browser.find_element_by_id("pass")
        username.send_keys(self._user)
        password.send_keys(self._password)
        self.browser.find_element_by_id("login_button").click()
        time.sleep(self.browser_pause_time * 4)

    def take_audios(self):
        with open(self.spreadsheet_filename, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.fieldnames)
            writer.writeheader()
            for audio, name, performer in self.audio_names_performers:
                if audio in self.used_audios or audio in self.rows:
                    continue
                self.click_on_specific_audio(audio)
                time.sleep(self.browser_pause_time)
                new_url = self.filter_new_mp3_url()
                row = {'name': name.group()}
                row['performer'] = performer.group()
                row['url'] = new_url
                row['audio_tag'] = audio
                self.rows.setdefault(audio, row)
                print(row)
                writer.writerow(row)
                self.used_urls.add(new_url)
                self.used_audios.add(audio)

    def parse_audio_names(self):
        self.audios = re.finditer(self.audio_pattern, self.browser.page_source)
        self.audio_names = re.finditer(self.audio_name_pattern, self.browser.page_source)
        self.audio_performers = re.finditer(self.audio_performer_pattern, self.browser.page_source)
        self.audio_names_performers = zip(self.audios, self.audio_names, self.audio_performers)

    def click_on_specific_audio(self, audio):
        while True:
            try:
                xpath = '//*[@id="{}"]/div/div[2]/div[3]'.format(audio.group())
                a = self.browser.find_element_by_xpath(xpath)
                a.click()
                time.sleep(self.browser_pause_time * 2)
                break
            except NoSuchElementException:
                # if unable to locate element, brobably we should scroll down to find it
                last_height = self.browser.execute_script("return document.body.scrollHeight")

                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(self.browser_pause_time / 2)
                new_height = self.browser.execute_script("return document.body.scrollHeight")
                if last_height == new_height:  # check if we stopped scrolling
                    break
            except WebDriverException as err:
                print(err)
                wait_time = self.browser_pause_time * 10
                print('waiting for {} s...'.format(wait_time))
                time.sleep(wait_time)
                # TODO: add counter here to break out of infinite loop if any
                break

    def download_audios(self):
        print('Starting to dowload audios...')
        with open(self.spreadsheet_filename, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for i, row in enumerate(reader):
                performer_folder = slugify(row.get('performer'))
                performer_folder_path = os.path.join(self.folder, performer_folder)
                if not os.path.exists(performer_folder_path):
                    os.mkdir(performer_folder_path)
                filename = '{}_{}'.format(row.get('name'),
                                          row.get('performer'))
                filename = slugify(filename) + '.mp3'
                filename = os.path.join(performer_folder_path, filename)
                if not os.path.isfile(filename):
                    os.system("gnome-terminal -e 'bash -c \"wget -O {} {}\"'".format(filename, row.get('url')))
                # TODO: important part, as we may not want to download *all* files simultaneously
                time.sleep(PAUSE_TIME)
                if i % 20 == 0:
                    time.sleep(5)
        print('All audios might have been downloaded successfully :)')

    def scroll_top(self):
        self.browser.execute_script("window.scrollTo(0, -document.body.scrollHeight);")
        time.sleep(self.browser_pause_time)

    def scroll_down(self):
        # Get scroll height
        last_height = self.browser.execute_script("return document.body.scrollHeight")
        c = 0
        while True:
            # Scroll down to bottom
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Wait to load page
            time.sleep(self.browser_pause_time)
            # Calculate new scroll height and compare with last scroll height
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                time.sleep(self.browser_pause_time)
                c += 1
                if c == 3:
                    time.sleep(self.browser_pause_time * 8)
                    break
            last_height = new_height
            # self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def filter_new_mp3_url(self):
        while True:
            try:
                self.all_requests = [entry['request']['url'] for entry in self.proxy.har['log']['entries']]
                music_urls = filter(self.mp3_url_pattern.search, self.all_requests)
                new_url = list(filter(lambda x: x not in self.used_urls, music_urls))
                assert len(new_url) == 1, 'there should be only one\n{}'.format(new_url)
                return new_url[0]
            except AssertionError:
                time.sleep(self.browser_pause_time)
                # TODO: add counter here to break out of infinite loop if any

    def load_existing_records(self):
        with open(self.spreadsheet_filename, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                self.rows.setdefault(row['audio_tag'], row)
            print('Loaded {} existing records form csv'.format(len(self.rows)))


def main():
    # url = 'https://vk.com/audios-1035609?section=all'  # smooth_jazz
    url = 'https://vk.com/audios-1196279'  # Кому Вниз
    parser = Parser(url,
                    user="380668483104",
                    password="fl4*9SM2n6",
                    folder='/media/shivan/Samsung/MUSIC/SmoothJazz')
    parser.create_csv_for_download()
    # TODO: if you want to actually DOWNLOAD all files, please set download_at_once to true.
    # TODO: otherwise only csv with audio urls will be created
    download_at_once = False
    if download_at_once:
        parser.download_audios()


if __name__ == '__main__':
    main()
