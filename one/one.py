# encoding=utf-8
"""
Reference: http://python.jobbole.com/84714/
"""

import json
import re
import time
import traceback
from multiprocessing import Pool
from typing import List

import bs4
import loguru
import pydantic
import requests
import typer

logger = loguru.logger

root_url = "http://wufazhuce.com"
cache_file = "one.json"
output_file = "one.txt"
default_start = 0
pool_num = 5
retry = 1
clean = 1

app = typer.Typer()


class Resource(pydantic.BaseModel):
    id: int
    volume: str or None = pydantic.Field(default="")
    imgUrl: str = pydantic.Field(default="")
    content: str = pydantic.Field(default="")


def get_newest_id():
    response = requests.get(root_url)
    soup = bs4.BeautifulSoup(response.text, "html.parser")

    container = soup.find("div", id="main-container")
    container = container.find_all(
        "a", href=re.compile("http://wufazhuce.com/one/[0-9]+")
    )

    max_id = 0
    for a in container:
        id_pattern = re.compile("[0-9]+")
        match = id_pattern.findall(a.get("href"))
        if match:
            id = int(match[0])
            if id > max_id:
                max_id = id

    return max_id


def get_vol(title):
    volume = None
    try:
        # print volume
        vol_pattern = re.compile("[0-9]+")
        match = vol_pattern.findall(title)
        if match:
            volume = match[0]
    except Exception as e:
        traceback.print_exc()
        logger.error("failed while volume={}".format(volume))
    return volume


def get_data(url) -> Resource:
    # get the id to identify the data
    id = url.split("/")[-1]

    data = Resource(id=int(id))
    data.volume = ""

    try:
        # visit url
        response = requests.get(url)

        # no data or can not reach, just return with id
        if not response.ok:
            return data

        # parse as html
        soup = bs4.BeautifulSoup(response.text, "html.parser")

        # get volume number from title
        title = soup.title.string
        volume = get_vol(title)
        data.volume = volume

        # one statement
        for meta in soup.select("meta"):
            if meta.get("name") == "description":
                # code mode may crash the statement, please do encode here
                data.content = meta.get("content").strip()

        # one image
        data.imgUrl = soup.find_all("img")[1]["src"].strip()

    except Exception as e:
        traceback.print_exc()

    return data


def load_cache(path) -> List[Resource]:
    try:
        with open(path, "r") as fp:
            data = json.load(fp)
            items = []
            for it in data:
                items.append(Resource(**it))
            return items

    except Exception as e:
        logger.warning("no cache file or get cache error")
        exit(1)


def timer(f):
    def wrapper(*args, **kwargs):
        start = time.time()
        res = f(*args, **kwargs)
        end = time.time()
        logger.info("cost {:.5}s to get new data".format(end - start))
        return res

    return wrapper


@timer
def get_resource(urls) -> List[Resource]:
    # run and crawl the data
    pool = Pool(pool_num)

    data = []
    # for u in urls:
    # item = get_data(u)

    for item in pool.map(get_data, urls):
        if not item:
            continue
        item: "Resource"
        print(item)
        data.append(item)
    return data


def to_url(key):
    # http://wufazhuce.com/one/4099
    return "{}/one/{}".format(root_url, key)


def get_keys(start, end, cache: List[Resource], refresh=False):
    pending = []
    existed = {i.id: i for i in cache}
    # plus 1 to include current end
    for key in range(start, end + 1):
        if key < 0:
            continue

        if key in existed:
            if existed[key].volume:
                continue

            if not refresh:
                continue

        # get url by the id we need
        pending.append(key)

    return pending


def dump(data: List[Resource], path):
    with open(path, "w+") as fd:
        # sort by the id aka volume in ascending order
        for item in data:
            # Code mode may crash the statement, please do encode here
            content = item.content
            if not content:
                continue
            # content = content.encode('utf-8')
            vol = item.volume
            if not vol:
                continue

            fd.write("vol.{}\n{}\n".format(vol, content))


@app.command()
def main(refresh: bool = typer.Option(False, "-r", "--refresh", is_flag=True, help="")):
    # get newest id
    newid = get_newest_id()
    logger.info("newest one is {0}".format(newid))

    # load exist data in JSON file
    cache: List[Resource] = load_cache(cache_file)

    # ready not exist url
    keys = get_keys(default_start, newid, cache, refresh=refresh)
    logger.info("pending keys: {}", keys)
    urls = [to_url(key) for key in keys]
    print(urls)
    logger.info("pending process urls count: {}".format(len(urls)))

    # get new data
    data = get_resource(urls)

    # log the number
    count_old = len(cache)
    count_new = len(data)
    logger.info("old cache number: {}".format(count_old))
    logger.info("new data number: {}".format(count_new))

    # combine all data
    data.extend(cache)

    data.sort(key=lambda x: x.id, reverse=True)

    # update dump file only when we have new data
    if count_new > 0:
        # dump the dict json data into file
        with open(cache_file, "w+") as outfile:
            raw = [i.model_dump() for i in data]
            json.dump(raw, outfile, indent=2, ensure_ascii=False)
            # json.dump(data, outfile, indent=4, ensure_ascii=False)

    # Output the data into a file.
    if count_new > 0:
        dump(data, output_file)


if __name__ == "__main__":
    app()
