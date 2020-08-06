# /usr/bin/env python3
# coding=utf-8
"""
python3 的爬虫模板
主要基于 requests_html 和 requests_file
"""
from requests_html import HTML, HTMLSession, Element
from requests_file import FileAdapter

import sys
import time
import traceback
import sh
import logging
import os
import re
import pandas as pd

from util.logger import logging

session = HTMLSession()
session.mount("file://", FileAdapter())


def get_page(url):
    # to bypass firewall
    if url.startswith("https"):
        res = session.get(url)
        res.html.render(sleep=5, reload=True)

    # to do the render
    if url.startswith("http"):
        res = session.get(url)
        res.html.render(sleep=5, reload=True)
    else:
        res = session.get(url)

    return res


def header_name(h):
    return h.text


def table_data(table):
    lines = []

    header = []
    for name in table.find('thead > tr > th'):
        header.append(name.text)

    if not header:
        return None

    rows = table.find('tbody > tr')

    df = pd.DataFrame(index=range(0, len(rows)), columns=header)
    for idx, row in enumerate(rows):
        line = []
        for td in row.find('td'):
            line.append(td.text)
        lines.append(line)
        df.loc[idx] = line

    # print(header, lines, )
    return df


def main():
    url = "https://docs.oracle.com/javase/8/docs/technotes/guides/security/StandardNames.html"

    filename = 'resource/Standard Algorithm Name Documentation.html'
    path = os.path.sep.join(
        (os.path.dirname(os.path.abspath(__file__)), filename))
    url = 'file://{}'.format(path)

    header2 = "#a0v1 > h2"
    header3 = "#a0v1 > h3"
    table = "#a0v1 > table"

    res = get_page(url)

    # get it now
    tags = res.html.find(header2) + res.html.find(header3)
    for h in tags:
        target = h.element.getnext().getnext()
        if target.tag == 'table':
            # process header
            name = header_name(h)
            # process table
            table = Element(element=target, url=url)
            data = table_data(table)

            if  data is None:
                continue
            if data.columns[0] != 'Algorithm Name':
                continue
            print('-'*20)
            print(name)
            column=data.iloc[:,0:-1]
            for index, row in column.iterrows():
                for t in row[0].split('\n'):
                    print(t)


if __name__ == "__main__":
    main()
