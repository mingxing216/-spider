# -*- coding:utf-8 -*-
import random


def get_ua():
    first_num = random.randint(55, 62)
    third_num = random.randint(0, 3200)
    fourth_num = random.randint(0, 140)
    os_type = [
        '(Windows NT 6.1; WOW64)', '(Windows NT 10.0; WOW64)', '(X11; Linux x86_64)',
        '(Macintosh; Intel Mac OS X 10_12_6)'
    ]
    chrome_version = 'Chrome/{}.0.{}.{}'.format(first_num, third_num, fourth_num)

    ua = ' '.join(['Mozilla/5.0', random.choice(os_type), 'AppleWebKit/537.36',
                   '(KHTML, like Gecko)', chrome_version, 'Safari/537.36']
                  )

    # ua = ''
    # if client == 'computer':
    #     first_num = random.randint(55, 62)
    #     third_num = random.randint(0, 3200)
    #     fourth_num = random.randint(0, 140)
    #     os_type = [
    #         '(Windows NT 6.1; WOW64)', '(Windows NT 10.0; WOW64)', '(X11; Linux x86_64)',
    #         '(Macintosh; Intel Mac OS X 10_12_6)'
    #     ]
    #     chrome_version = 'Chrome/{}.0.{}.{}'.format(first_num, third_num, fourth_num)
    #
    #     ua = ' '.join(['Mozilla/5.0', random.choice(os_type), 'AppleWebKit/537.36',
    #                    '(KHTML, like Gecko)', chrome_version, 'Safari/537.36']
    #                   )
    # elif client == 'phone':
    #     ua_list = [
    #         'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1',
    #         'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1',
    #         'Mozilla/5.0 (Linux; Android 5.0; SM-G900P Build/LRX21T) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Mobile Safari/537.36',
    #         'Mozilla/5.0 (Linux; Android 8.0.0; Pixel 2 XL Build/OPD1.170816.004) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Mobile Safari/537.36',
    #         'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Mobile Safari/537.36'
    #     ]
    #     ua = random.choice(ua_list)

    return ua
