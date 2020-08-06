# /usr/bin/env python3
from requests_html import HTML, HTMLSession
from requests_file import FileAdapter

import sys
import time
import traceback
import sh
import os
import re

from util.util import CrawlSession
from util.logger import logging


class CVEDetialSession(CrawlSession):
    root = "https://www.cvedetails.com"
    search_product = "https://www.cvedetails.com/product-search.php?vendor_id=0&search={}"
    search_cve = "https://www.cvedetails.com/cve-details.php?t=1&cve_id={}"

    def __init__(self):
        super(CVEDetialSession, self).__init__(self)
        self.render = False

    def get_product_url(self, product):
        url = self.search_product.format(product)
        r = self.get(url)
        logging.info(url)

        item = r.html.find(
            '.listtable > tbody > tr:nth-child(2) > td:nth-child(4) > a', first=True)

        href = item.attrs['href']
        logging.info(href)

        url = "{}{}".format(self.root, href)
        return url
        

    def get_product_name_in_list(self, url):
        r = self.get(url)
        logging.info(url)

        items = r.html.find(
            '#contentdiv > table > tbody > tr > td.listtablecontainer > form > table > tbody > tr > td:nth-child(1) > a')

        names = [i.text for i in items]
        logging.info(names[:10])

        return names

        

    # def get_cve_lib():
    #     prefix = "https://www.cvedetails.com/vendor/firstchar-L/"
    #     suffix = "/?sha=3cae7a4e749f90be1a19651d1d67f209653e4dfe&trc=615&order=1"
    #     urls = ["{}{}{}".format(prefix, i, suffix) for i in range(1, 8)]
    #     for url in urls:
    #         res = requests.get(url)
    #         soup = bs4.BeautifulSoup(res.text, "html.parser")

    #         form = soup.find('form', attrs={'action': "/vendor-match.php", 'method': "get"})
    #         # <form action="/vendor-match.php" method="get">
    #         table = form.find('table', attrs={'class': 'listtable'})
    #         # <table class="listtable">
    #         target = table.find_all('a', text=re.compile("(l|L).*"))
    #         for a in target:
    #             name = a.text
    #             print name.strip()

    def get_cve(self, url):
        res = self.get(url)
        links = []

        target = res.html.find('div #searchresults a ')
        for a in target:
            for link in a.links:
                # if re.match("/cve/CVE-[0-9.-]+/", cve):
                if 'cve/CVE' in link:
                    print(link)
                    links.append(link)
        return links

    @staticmethod
    def get_url(href):
        return "{}/{}".format(CVEDetialSession.root, href)

    def get_define(self, links, after=None,before=None,stop=None):
        pattern = re.compile(r'[0-9a-fA-F]{40}')
        for link in links:
            if stop:
                if str(stop) in link:
                    break

            cve_url = self.get_url(link)
            git_url = None
            r = self.get(cve_url)

            for a in r.html.find('#cvedetails > div.cvedetailssummary'):
                print(a.text)
                break

            for a in r.html.find('#vulnrefstable a'):
                for url in a.absolute_links:
                    if pattern.search(url):
                        git_url = url
                        break

            print(cve_url)
            print(git_url)
            print()


def main():
    # get_cve_lib()
    # get_product('openssl')

    session = CVEDetialSession()
    url = 'https://www.cvedetails.com/vulnerability-list/vendor_id-217/Openssl.html'
    url = 'https://www.cvedetails.com/vulnerability-list/vendor_id-72/product_id-1820/GNU-Zlib.html'
    url = 'https://www.cvedetails.com/vulnerability-list/vendor_id-72/product_id-1394/GNU-TAR.html'
    url = 'https://www.cvedetails.com/vulnerability-list/vendor_id-7294/product_id-12271/Libpng-Libpng.html'
    url = 'https://www.cvedetails.com/vulnerability-list/vendor_id-26/product_id-739/Microsoft-Windows-Xp.html'
    # cve_links = session.get_cve(url)
    # session.get_define(cve_links)

    url_on_page = 'https://www.cvedetails.com/product-list/product_type-/vendor_id-0/firstchar-L/page-{}/products.html?sha=416e0d8b2e3df304a1fbfaf83676ba5ec96902e1&trc=1957&order=1'

    session.render=True
    names  =[]
    for page in range(14,26):
        url = url_on_page.format(page)
        names += session.get_product_name_in_list(url)
        time.sleep(10)
    with open('cve_product_name_list.pkl','wb') as fd:
        import pickle
        pickle.dump(names, fd)
        print(names)

if __name__ == '__main__':
    main()
