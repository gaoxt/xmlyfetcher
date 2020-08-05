# -*- coding:utf-8 -*-

import requests
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool, Lock, freeze_support
import os
import sys


def input_page_url_with_change_dir():
    print('请输入存储文件夹(回车确认):')
    while True:
        dir_ = input()
        if os.path.exists(dir_):
            os.chdir(dir_)
            break
        else:
            try:
                os.mkdir(dir_)
                os.chdir(dir_)
                break
            except Exception as e:
                print('请输入有效的文件夹地址:')

    print('请输入想下载FM页面的网址 或者 albumid(回车确认) -\n'
          '如 http://www.ximalaya.com/20251158/album/2758791：')
    page_url = input()
    return page_url


page_url = input_page_url_with_change_dir()
page_url = 2758791

headers = {
    'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                   'Chrome/57.0.2987.133')
}


def get_json_urls_from_page_url(page_url):
	# 检测page_url 如果是存数字则是albumid 否则当 网址处理
	xmly_album_list = "http://www.ximalaya.com/revision/album/getTracksList?albumId=%d&pageNum=1" % page_url
	res = requests.get(xmly_album_list, headers=headers).json()
	page_count = res['data']['trackTotalCount']
	page_data = res['data']['tracks']
	for item in page_data:
		urls = "http://www.ximalaya.com/tracks/%d.json" % item['trackId']
	return urls


mp3_json_urls = get_json_urls_from_page_url(page_url)
n_tasks = len(mp3_json_urls)
lock = Lock()
shared_dict = {}
def get_mp3_from_json_url(json_url):
    mp3_info = requests.get(json_url, headers=headers).json()
    title = mp3_info['album_title'] + '+ ' + mp3_info['title'] + '.m4a'
    path = mp3_info['play_path']
    title = title.replace('|', '-')  # 避免特殊字符文件名异常

    if os.path.exists(title):
        return 'Already exists!'

    while True:
        try:
            with open(title, 'wb') as f:
                response = requests.get(path, headers=headers, stream=True)

                if not response.ok:
                    # shared_dict.pop(title)
                    print('response error with', title)
                    continue

                total_length = int(response.headers.get('content-length'))

                chunk_size = 4096
                dl = 0
                shared_dict[title] = 0

                for block in response.iter_content(chunk_size):
                    dl += len(block)
                    f.write(block)
                    done = int(50 * dl / total_length)
                    shared_dict[title] = done

                global n_tasks
                with lock:
                    n_tasks -= 1
                shared_dict.pop(title)
                return 'Done!'

        except Exception as e:
            print('other error with', title)
            os.remove(title)


def report_status():
    import time
    n = len(mp3_json_urls)

    print(u'准备下载...')
    while len(shared_dict) == 0:
        time.sleep(0.2)

    while len(shared_dict) != 0:
        line = ''  # "\r"
        for title, done in shared_dict.items():
            line += "%s\n - [%s%s]\n" % (
                title, '=' * done, ' ' * (50 - done)
            )
        line += '\n**** 剩余/总任务 = %s/%s ****' % (n_tasks, n)
        os.system('cls')
        sys.stdout.write(line)
        sys.stdout.flush()
        time.sleep(1)


freeze_support()
with Pool(6) as pool:
    r = pool.map_async(get_mp3_from_json_url, mp3_json_urls)
    report_status()
    r.wait()
    os.system('cls')
    print('下载完成！')