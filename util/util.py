import sys
import time
import traceback
import types
import os
import re
import requests
from collections import OrderedDict

import wget
import sh
from bs4 import *
from requests_html import HTML, HTMLSession
from requests_file import FileAdapter
from concurrent.futures import ThreadPoolExecutor

from .logger import logging


class CrawlSession(HTMLSession):
    def __init__(self, cache=True, render=True):
        super(CrawlSession, self).__init__()
        self.mount('file://', FileAdapter())

        # if cache, all html will be dumped into file using md5
        # furthermore, is cached, use cache (file://) but http
        self.cache = cache
        self.render = render
        self.render_sleep = 5

    def get(self, url, render=None, *args,**kwargs):
        if self.cache:
            pass
        response = super(CrawlSession, self).get(url,*args,**kwargs)
        if self.render or render:
            response.html.render(sleep=self.render_sleep, keep_page=True, reload=True)
        return response

    def download(self, file_urls, dir='.'):
        """
        parallel download files into output dir
        """

        def do_download(url, name):
            print(url)
            print(dir)
            print(name)
            # return

            path = '{}/{}'.format(dir, name)
            if os.path.exists(path):
                logging.info('exist: {}'.format(name))
            else:
                logging.warning('will download: {}'.format(path))
                try:
                    # the wget module works not good enough
                    # res = wget.download(url, path)
                    # wget = sh.Command('wget')
                    # res = wget([url, '-P', dir, '-O', name])
                    curl = sh.Command('curl')
                    res = curl([url, '-o', '{}/{}'.format(dir,name)])
                except Exception as e:
                    traceback.print_exc()
                    logging.warning('download failed:{} {}'.format(url, dir, name))
                    return None

                logging.warning('download success: {}'.format(path))
                return path

        if not os.path.exists(dir):
            os.makedirs(dir)

        with ThreadPoolExecutor(max_workers=1) as executor:
            for name, url in file_urls.items():
                executor.submit(do_download, url, name)

        logging.info('completed')

    def get_download_url3(self, url, pattern):
        """
        crawl url related to the file
        return a mapping: Dict[filename->url]
        """

        from urllib import parse

        page = self.get(url)

        file_urls = {}
        pattern = re.compile(pattern)

        # # find href
        # container = page.html.find('a[href$=".pdf"]')
        # for i in container:
        #     href = i.attrs["href"]
        #     if not pattern.match(href):
        #         continue

        #     target = "{}/{}".format(url, href)
        #     file_urls[href]=target

        # get link directly
        for url in page.html.absolute_links:
            name = url.split('/')[-1]
            if not pattern.match(name):
                continue
            name = parse.unquote(name)
            file_urls[name] = url
        print(file_urls)
        return file_urls

    def get_download_url2(self, url):
        """
        crawl url related to the file
        return a mapping: Dict[filename->url]
        """
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')

        file_urls = {}

        # TODO: set dest tag here: re or plain
        container = soup.find_all('a', href=re.compile(".*\.pdf"))
        for i in container:
            href = i.get("href")
            target = "{}/{}".format(url, href)
            file_urls[href] = target
        return file_urls


class CrawlItemSession(CrawlSession):
    
    def get_item(self, url, selector):
        r = self.get(url)
        found = r.html.find(selector)
        return found

    def get_item_text(self, url, selector):
        r = self.get(url)
        found = r.html.find(selector)

        res = []
        for i in found:
            res.append(i.text)
        return res

    def get_item_attr(self, url, selector, attr, keying=None):
        """
        return the ordered dict,
        default key=value aka the attribute
        otherwise using the given keying generator
        """
        r = self.get(url)
        found = r.html.find(selector)
        data = OrderedDict()
        for i in found:
            if attr not in i.attrs:
                continue
            if isinstance(keying, types.GeneratorType):
                key = next(keying)
                value = i.attrs[attr]
                data[key] = value
            else:
                value = i.attrs[attr]
                value = value.split('/')[-1]
                data[key] = value
        return data
