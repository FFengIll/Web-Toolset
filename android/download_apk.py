# coding=utf-8
import os, sys
import requests
import json
from queue import Queue
import urllib.request as urllib2
import time
from pprint import *
import sh
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Pool
from requests_html import HTMLSession

OVERWRITE = False


class Market:
    def __init__(self):
        self.session = HTMLSession()
        self.pool = ProcessPoolExecutor(max_workers=5)

    def download(self, *args):
        pass


def download(url, package):
    if os.path.exists(package) :
        return
    print(url)
    cmd = "curl -o {} -L {}".format(package, url)
    print(cmd)
    os.system(cmd)

    # curl = sh.Command('curl')
    # cmd = "-o {} -L {}".format(package, url)
    # curl(cmd.split(' '))

def get_content_size(url, proxy=None):
    """
    通过head方法，仅获取header，并从中抽取必要信息，而不必大量IO，获取content
    :param url:
    :param proxy:
    :return:
    """
    res = requests.head(url, timeout=10, allow_redirects=False)
    size = res.headers["Content-Length"]
    return int(size)


def get_redirect_url(url, try_count=1):
    """
    禁止自动处理重定向，并从重定向的location中获取目标url
    :param url:
    :param try_count:
    :return:
    """
    res = requests.get(url, timeout=10, allow_redirects=False)
    return res.headers["location"]


class Mi(Market):
    def __init__(self):
        super(Mi, self).__init__()

        self.music_category = (
            "http://m.app.mi.com/categotyAllListApi?categoryId=27&page=0&pageSize={}"
        )
        self.all = "http://m.app.mi.com/categotyAllListApi?page=0&pageSize={}"

    def batch_download(self, data, limit, output="./", debug=False):
        urls = []
        wait = Queue()
        count = 0
        for i in data["data"]:
            count += 1
            if count >= limit:
                break
            # 基于id可以定位url
            id = i["appId"]
            url = "http://m.app.mi.com/download/{id}?dcp=page%3Ddetail%26id%3D{id}".format(
                id=id
            )

            # 存在重定向
            url = get_redirect_url(url)
            name = url.split("/")[-1]
            size = get_content_size(url)
            print(url)

            # 把数据存下来备用
            i["realURL"] = url
            i["realName"] = name
            i["realSize"] = size

            print(i["displayName"])

            if size == 0 or size > 500 * 1024 * 1024:
                continue

            if debug:
                pprint(url)
            else:
                f = self.pool.submit(download, url, os.path.join(output, name))
                wait.put(f)

        while not wait.empty():
            f = wait.get()
            if f.done():
                continue

    def collect(self, url):
        res = self.session.get(url)
        data = res.text
        data = json.loads(data)
        return data


class QQ(Market):
    read_category = "https://sj.qq.com/myapp/category.htm?orgame=1&categoryId=102"
    news_category = "https://sj.qq.com/myapp/category.htm?orgame=1&categoryId=110"
    music_category = "https://sj.qq.com/myapp/category.htm?orgame=1&categoryId=101"
    video_category = "https://sj.qq.com/myapp/category.htm?orgame=1&categoryId=103"
    finance_category = "https://sj.qq.com/myapp/category.htm?orgame=1&categoryId=114"
    shop_cate = "https://sj.qq.com/myapp/category.htm?orgame=1&categoryId=122"

    all = "https://sj.qq.com/myapp/category.htm?orgame=1"

    def __init__(self):
        super().__init__()

    def collect_all(self, limit=0):
        cates = [
            self.read_category,
            self.news_category,
            self.music_category,
            self.video_category,
            self.finance_category,
            self.shop_cate,
        ]
        urls = []
        for c in cates:
            urls += self.collect(c, limit)
            if len(urls) > limit:
                break
        return urls

    def collect(self, url, limit=0):
        res = self.session.get(url)

        select = "body > div.category-wrapper.clearfix > div.main > ul > li > div > div > a.name.ofh"
        res = res.html.find(select)

        root = "https://sj.qq.com/myapp/"

        data = []
        for idx, item in enumerate(res):
            if limit and idx > limit:
                break
            tmp = root + item.attrs["href"]
            data.append(tmp)
        return data

    def batch_download(self, data, limit, debug=False):
        urls = []
        wait = Queue()
        count = 0
        selector = "#J_DetDataContainer > div > div.det-ins-container.J_Mod > div.det-ins-btn-box > a.det-ins-btn"
        for url in data:
            count += 1
            if count >= limit:
                break

            response = self.session.get(url)

            item = response.html.find(selector, first=True)
            url: str = item.attrs["ex_url"].strip()
            apk = item.attrs["apk"].strip()
            name = "{}.apk".format(apk)
            print(url, apk)
            if debug:
                pprint(url)
            else:
                f = self.pool.submit(download, url, name)
                wait.put(f)

        while not wait.empty():
            f = wait.get()
            if f.done():
                continue


import click


@click.command()
@click.option(
    "--debug", "-D", default=False, type=click.types.BOOL, help="use debug mode"
)
@click.option("--limit", "-L", default=10, type=click.types.INT, help="limit number")
@click.option(
    "--overwrite", "-O", default=False, type=click.types.BOOL, help="overwrite"
)
def main(debug=False, limit=10, overwrite=False):
    global OVERWRITE
    OVERWRITE = overwrite

    tool = Mi()
    urls = tool.collect(
        "http://m.app.mi.com/searchapi?keywords=%E9%98%BF%E9%87%8C&pageIndex=0&pageSize=300"
    )
    with open("resource/阿里系apk.json") as fd:
        urls = json.load(fd)

        tool.batch_download(urls, limit=1000, debug=debug, output="download/alibaba-apk")
    return

    tool = Mi()
    urls = tool.collect(tool.all.format(limit))
    pprint(urls)
    tool.batch_download(
        urls, limit, debug=debug,
    )

    tool = QQ()
    urls = tool.collect_all(limit=limit)
    # urls = tool.collect(tool.all, limit=limit)
    pprint(urls)
    tool.batch_download(urls, limit, debug=debug)


if __name__ == "__main__":
    main()
