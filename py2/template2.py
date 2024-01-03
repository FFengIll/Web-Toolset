# /usr/bin/env python2
# coding=utf-8
'''
python2 的爬虫模板
主要记住bs4
'''
import requests
from  bs4 import *
import re
import wget
import os, sys


def download(url, filename=None):
    if os.path.exists(filename):
        return True
    else:
        #TODO: set download to where, default pwd
        wget.download(url)


def spider_all(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')

    # TODO: set dest tag here: re or plain
    container = soup.find_all('a', href=re.compile(".*\.pdf"))
    for i in container:
        href = i.get("href")
        target = "{}/{}".format(url, href)
        print(target)
        download(target, filename=href)


def main():
    # TODO: set dest url here: url
    url = "http://www.cs.cmu.edu/afs/cs.cmu.edu/academic/class/15745-s14/public/lectures/"
    spider_all(url)


if __name__ == '__main__':
    main()
