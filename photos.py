from audios import Parser


def main():
    url = 'https://vk.com/albums133545646'  # Яни
    parser = Parser(url,
                    user="USERNAME",
                    password="PASSWORD",
                    folder='/path/to/folder',
                    mode='photo',
                    login_url='https://vk.com/audios-1035609')
    parser.download_photos()


if __name__ == '__main__':
    main()
