# /usr/bin/env python3
import sys
import time
import traceback
import os
import re

from util.util import CrawlItemSession
from util.logger import logging


def main():
    session = CrawlItemSession()

    home_url = 'http://www.cs.cmu.edu/afs/cs.cmu.edu/academic/class/15745-s14/public/lectures/'
    home_url = 'https://www.cl.cam.ac.uk/teaching/2006/OptComp/slides/'
    OUTPUT_DIR = 'output/Numerical Analysis (3SK3)-McMaster-Xiaolin Wu'
    # OUTPUT_DIR = 'pdf'

    home_url = 'http://www.ece.mcmaster.ca/~xwu/outline3SK3.htm'

    url = home_url
    file_urls = session.get_download_url3(url, pattern=".*\.pdf")
    print(file_urls)
    session.download(file_urls, dir=OUTPUT_DIR)


if __name__ == '__main__':
    main()
