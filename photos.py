from audios import Parser


def main():
    # url = 'https://vk.com/audios-1035609?section=all'  # smooth_jazz
    # url = 'https://vk.com/audios-1196279'  # Кому Вниз
    # url = 'https://vk.com/audios111954336'  # Яни
    url = 'https://vk.com/albums111954336'  # Яни
    parser = Parser(url,
                    user="380668483104",
                    password="fl4*9SM2n6",
                    folder='/media/shivan/7C40325F40322076/2_MUSIC/Yana',
                    mode='photo',
                    login_url='https://vk.com/audios-1035609')
    parser.download_photos()


if __name__ == '__main__':
    main()
