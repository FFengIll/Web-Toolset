# /usr/bin/env python3
# coding=utf-8
'''
python3 的爬虫模板
主要基于 requests_html 和 requests_file
'''
from requests_html import HTML, HTMLSession
from requests_file import FileAdapter

import sys
import time
import traceback
import sh
import logging
import os
import re

from util.logger import logging



session = HTMLSession()
session.mount('file://', FileAdapter())


def get_page(url, selector):
    
    # to bypass firewall
    if url.startswith('https'):
        res = session.get(url)
        res.html.render(sleep=5, reload=True)
    
    # to do the render
    if url.startswith('http'):
        res = session.get(url)
        res.html.render(sleep=5, reload=True)
    else:
        res = session.get(url)

    # get it now
    tag = res.html.find(selector)
    for a in tag:
        href = a.text
        print(a.text)


def main():
    url = 'https://www.seebug.org/category/'

    filename = 'test.html'
    path = os.path.sep.join(
        (os.path.dirname(os.path.abspath(__file__)), filename))
    url = 'file://{}'.format(path)

    selector = '#category-list > li > a'

    get_page(url, selector)


if __name__ == '__main__':
    main()
