import csv
import os
import time

import re
from pprint import pprint

from selenium import webdriver
from browsermobproxy import Server

py_location = os.path.realpath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
src_path = os.path.join(py_location, 'src')
CHROMEDRIVER_PATH = os.path.join(src_path, 'chromedriver')
BROWSERMOBPROXY_PATH = os.path.join(src_path, 'browsermob-proxy-2.1.4/bin/browsermob-proxy')
PAUSE_TIME = 0.5


class Parser():
    def __init__(self, url, user, password, folder: str = ''):
        self.folder = folder or py_location
        self._user = user
        self._password = password
        self.url = url
        self.audio_name_pattern = re.compile(
            r'(?<=class="audio_title_inner" tabindex="0" nodrag="1" aria-label=")[^"]*')
        self.audio_performer_pattern = re.compile(r'(?<=class="audio_performer">)[^<]*')
        self.audio_pattern = re.compile(r'(audio_-\d*_\d*)')
        self.filename_pattern = re.compile(r'(?<=audios-)\d*(?=\?)')
        self.fieldnames = ['name', 'performer', 'url']
        self.browser_pause_time = PAUSE_TIME

        audios_number = self.filename_pattern.search(self.url).group()
        self.filename = 'audios_list_{}.csv'.format(audios_number)
        self.proxy = None
        self.browser = None
        self.setup_selenium()

    def setup_selenium(self):
        server = Server(BROWSERMOBPROXY_PATH)
        server.start()
        self.proxy = server.create_proxy({'captureHeaders': True, 'captureContent': True, 'captureBinaryContent': True})
        service_args = ["--proxy=%s" % self.proxy.proxy, '--ignore-ssl-errors=yes']
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--proxy-server={0}".format(self.proxy.proxy))
        self.browser = webdriver.Chrome(CHROMEDRIVER_PATH, service_args=service_args, chrome_options=chrome_options)
        self.proxy.new_har()

    def run(self):
        if os.path.exists(self.filename):
            print('File with urls seems to exist in the folder...')
        else:
            self.browser.get(self.url)

            username = self.browser.find_element_by_id("email")
            password = self.browser.find_element_by_id("pass")

            username.send_keys(self._user)
            password.send_keys(self._password)

            self.browser.find_element_by_id("login_button").click()
            time.sleep(self.browser_pause_time * 4)
            self.scroll_down()

            self.parse_audio_names()

            self.click_on_all_audios()
            time.sleep(self.browser_pause_time * 4)
            self.all_requests = [entry['request']['url'] for entry in self.proxy.har['log']['entries']]

            self.filter_music()
            self.build_download_csv()

    def build_download_csv(self):
        with open(self.filename, 'w') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.fieldnames)
            writer.writeheader()
            for audio in self.audios:
                row = {'name': self.audio_names_dict.get(audio)}
                row['performer'] = self.audio_performers_dict.get(audio)
                row['url'] = self.music_urls_dict.get(audio)
                writer.writerow(row)

    def parse_audio_names(self):
        self.audios = re.findall(self.audio_pattern, self.browser.page_source)
        self.audio_names = re.findall(self.audio_name_pattern, self.browser.page_source)
        self.audio_performers = re.findall(self.audio_performer_pattern, self.browser.page_source)
        self.audio_names_dict = dict(zip(self.audios, self.audio_names))
        self.audio_performers_dict = dict(zip(self.audios, self.audio_performers))
        pprint(self.audio_names_dict)
        pprint(self.audio_performers_dict)

    def click_on_all_audios(self):
        for audio in self.audios:
            a = self.browser.find_element_by_xpath(
                '//*[@id="{}"]/div/div[2]/div[3]'.format(audio))
            a.click()
            time.sleep(1)

    def download_audios(self):
        with open(self.filename, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                filename = '{}_{}.mp3'.format(row.get('name'),
                                              row.get('performer'))
                print(filename)
                if not os.path.isfile(filename):
                    os.system("gnome-terminal -e 'bash -c \"wget -O {} {}\"'".format(filename, row.get('url')))

    def filter_music(self):
        import re
        r = re.compile("mp3\?extra=")
        pprint(self.all_requests)
        self.music_urls = filter(r.search, self.all_requests)
        # TODO: fix possible bug - it seems like self.music_urls can be LESSER than self.audios
        self.music_urls_dict = dict(zip(self.audios, self.music_urls))

    def scroll_down(self):
        # Get scroll height
        last_height = self.browser.execute_script("return document.body.scrollHeight")

        while True:
            # Scroll down to bottom
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(self.browser_pause_time)

            # Calculate new scroll height and compare with last scroll height
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            # self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")


def main():
    # TODO: add proper command line arguments
    url = 'https://vk.com/audios-1035609?section=all'
    parser = Parser(url, user="VK_USERNAME", password="VK_PASSWORD")
    parser.run()

    print('All audios might have been downloaded successfully :)')
    input('Press any key to continue...')


if __name__ == '__main__':
    main()
