# -*- coding:utf-8 -*-
'''
Reference: http://python.jobbole.com/84714/
'''

import argparse
import re
from multiprocessing import Pool
import requests
import bs4
import time
import json
import io
import traceback
import logging

logging.root.setLevel(logging.INFO)

root_url = 'http://wufazhuce.com'
cache_file = "Cache"
output_file = "One.txt"
default_count = 1000
pool_num = 5
retry = 1
clean = 1


def get_url(num):
    url = '{}/one/{}'.format(root_url, num)
    return url


def get_new_id():
    response = requests.get(root_url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")

    container = soup.find('div', id="main-container")
    container = container.find_all(
        'a', href=re.compile("http://wufazhuce.com/one/[0-9]+"))

    newest = 0
    for a in container:
        idre = re.compile("[0-9]+")
        id = idre.findall(a.get('href'))

        res = int(id[0])
        if (res > newest):
            newest = res

    return newest


def get_vol(title):
    volume = title
    try:
        # print volume
        revolume = re.compile("[0-9]+")
        newvol = revolume.findall(volume)
        # print newvol
        if (newvol.__len__() > 0):
            volume = newvol[0]
            # print "new",volume
    except Exception, e:
        print e
        print volume
    return volume


def get_data(url):
    data = {}

    # get the id to identify the data
    id = url.split('/')[-1]
    data['id'] = id
    data['volume'] = None

    try:
        # visit url
        response = requests.get(url)

        # no data or can not reach, just return with id
        if response.status_code != 200:
            return data

        # parse as html
        soup = bs4.BeautifulSoup(response.text, "html.parser")

        # title
        title = soup.title.string

        # get volume number from title
        volume = get_vol(title)
        data["volume"] = volume

        # one statement
        for meta in soup.select('meta'):
            if meta.get('name') == 'description':
                # code mode may crash the statement, please do encode here
                data["content"] = meta.get('content').strip()

        # one image
        data["imgUrl"] = soup.find_all('img')[1]['src'].strip()

    except Exception, e:
        traceback.print_exc()

    return data


def load_cache(file):
    try:
        with open(file) as fp:
            data = json.load(fp)
            data = json.loads(data)
    except Exception, e:
        return {}

    return data


def process_urls(urls):
    pool = Pool(pool_num)

    # run and crawl the data
    start = time.time()
    dataList = pool.map(get_data, urls)
    end = time.time()
    logging.info("cost {}s to get new data".format(end - start))

    dataDict = {}
    for item in dataList:
        dataDict[item['id']] = item
    return dataDict


def get_urls(exist_data, newest, count):
    pending = []
    for key in range(newest - count, newest + 1):
        if key < 0:
            continue

        if str(key) in exist_data:
            if exist_data[str(key)]['volume']:
                continue

        # get url by the id we need
        url = get_url(key)
        pending.append(url)

    return pending


def output(data):
    # sort them into a list
    data_list = list(data)
    # sort by the id aka volume in ascending order
    data_list.sort(key=lambda x: -int(x))
    with open(output_file, "w") as fd:
        for key in data_list:
            item = data[key]

            # Code mode may crash the statement, please do encode here
            content = item.get("content", '')
            content = content.encode('utf-8')
            vol = item.get("volume", '')
            vol = "vol." + str(vol).encode("utf-8")

            fd.write('{}\n{}\n'.format(vol, content))


def main():
    # get newest id
    newest = get_new_id()
    logging.info("newest one is {0}".format(newest))

    # load exist data in JSON file
    cache = load_cache(cache_file)

    # ready not exist url
    urls = get_urls(cache, newest, count=default_count)
    logging.info('urls count: {}'.format(len(urls)))

    # get new data
    new_data = process_urls(urls)

    # log the number
    oldnumber = len(cache)
    newnumber = len(new_data)

    # retry to get the data, so we should drop the old invalid data
    data = {}
    data.update(cache)
    data.update(new_data)

    # update dump file only when we have new data
    if (newnumber > 0):
        # dump the object into json string
        jsonData = json.dumps(data)

        # dump the json string into file
        with open(cache_file, 'w') as outfile:
            json.dump(jsonData, outfile)

    logging.info("old cache number: {}".format(oldnumber))
    logging.info("new data number: {}".format(newnumber))

    # Output the data into a file.

    output(data)


if __name__ == '__main__':
    main()
