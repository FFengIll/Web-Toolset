from requests_html import HTML, HTMLSession
from requests_file import FileAdapter

import sys
import time
import traceback
import sh
import logging
import os
import json
from concurrent import futures

console = logging.StreamHandler(sys.stdout)
console.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s %(filename)s [%(lineno)d] %(levelname)s: %(message)s', )
formatter = logging.Formatter(
    '%(asctime)s %(filename)s [%(lineno)d] %(levelname)s: %(message)s', datefmt='%Y-%m-%d, %a, %H:%M:%S')
console.setFormatter(formatter)

logger = logging.getLogger('test')
logger.setLevel(logging.DEBUG)
logger.addHandler(console)
logging = logger

root_url = 'https://etherscan.io'
token_url = 'https://etherscan.io/tokens'
address_url = 'https://etherscan.io/address'
search_url = "https://etherscan.io/search?q="

eidoo_url = "https://erc20-tokens.eidoo.io/"

delay = True
update = False


class ICOCrawlSession(HTMLSession):
    def __init__(self):
        super(ICOCrawlSession, self).__init__()
        self.mount('file://', FileAdapter())

        logging.info("init to bypass DDOS firewall")
        r = self.get(token_url)
        r.html.render(sleep=6, reload=True)

    @staticmethod
    def get_valid_name(names):
        res = []
        for item in names:
            s = item.split(' ')[0]
            res.append(s)
        return res

    @staticmethod
    def regular_name(path):
        """
        we must standard filename for future use
        no (), no space
        so name is
        longname.shortname.address.sol
        """

        path2 = path.replace('(', '.')
        path2 = path2.replace(' ', '')
        path2 = path2.replace(')', '').replace('b\'', '').replace('\'', '')

        return path2

    @staticmethod
    def filter_by_name(names, exist_name):
        res = set()
        tmp = set()

        # filter by file stat
        output = sh.ls('ICO').stdout.decode('utf-8')
        for item in names:
            if item in output:
                continue
            else:
                tmp.add(item)

        # filter by history
        for item in tmp:
            found = False
            for e in exist_name:
                if item in e:
                    found = True
                    break
            if not found:
                res.add(item)
        return res

    @staticmethod
    def filter_by_address(hrefs, exist_addr):
        logging.debug("possible ref no:{}".format(len(hrefs)))

        urls = set()
        for item in hrefs:
            try:
                address = item.split('/').pop()
                if address in exist_addr:
                    continue
                else:
                    urls.add(item)
            except:
                pass

        logging.debug("filtered ref no:{}".format(len(urls)))
        return urls

    def get_token_info(self, url):
        r = self.get(url)

        if delay:
            time.sleep(1)

        code_div = r.html.find("div[id='dividcode'] pre[id='editor']", first=True)
        solidity = code_div.full_text
        solidity = str(solidity)

        summary_div = r.html.find(
            "div[id='ContentPlaceHolder1_divSummary']", first=True)

        info_a = summary_div.find(
            "#ContentPlaceHolder1_tr_tokeninfo > td:nth-child(2) > a", first=True)
        name = info_a.text

        address = info_a.attrs['href'].split('/').pop()

        # never keep any space char
        return name.strip(), address.strip(), solidity.strip()
        # return name.strip().replace(' ',''), address.strip().replace(' ',''), solidity.strip().replace(' ','')

    def get_token_url(self, url, exist_addr):
        r = self.get(url)
        table = r.html.find(
            "#ContentPlaceHolder1_divresult > table tbody", first=True)
        links = table.find("a[href]")

        hrefs = set()
        for item in links:
            href = item.attrs['href']
            href = str(href).replace('token', 'address')
            hrefs.add(href)

        hrefs = self.filter_by_address(hrefs, exist_addr)
        urls = ['{}{}'.format(root_url, href) for href in hrefs]

        return urls

    def get_page_no(self, ):
        page_no = 10
        # r = self.get(token_url)
        return page_no

    def get_eidoo_list(self, ):
        logging.info("get eidoo list")

        if update or not os.path.isfile('eidoo.html'):
            logging.info('get from http://*')
            r = self.get(eidoo_url)
            r.html.render()

            with open('eidoo.html', 'w+') as fd:
                fd.write(r.text)
        else:
            logging.info('get from file://*')
            path = os.path.sep.join(
                (os.path.dirname(os.path.abspath(__file__)), 'eidoo.html'))
            url = 'file://{}'.format(path)
            r = self.get(url)

        table = r.html.find("table#tokensTable", first=True)

        row = table.find("tr td[class='coin'] h4")

        logging.info("get coin names")
        coin_name = []
        for item in row:
            name = item.text
            coin_name.append(name)
        return coin_name

    def get_address(self, url):
        r = self.get(url)
        div = r.html.find("div[id='ContentPlaceHolder1_divSummary']", first=True)
        address = div.find(
            "table tr[id='ContentPlaceHolder1_trContract'] a[href]", first=True)
        address = address.text
        return address

    def search_erc20(self, name):
        res = None

        r = self.get('{}{}'.format(search_url, name))
        if delay:
            time.sleep(1)
        url = r.url
        if 'token' in url:
            try:
                address = self.get_address(url)
                url = "{}/{}".format(address_url, address)
                logging.info(url)
                res = url
            except:
                logging.error('error ignore {}'.format(name))
        else:
            with open("ICO/{}".format(name), 'w+') as fd:
                fd.write('')
                logging.info('ignore {}'.format(name))

        return res

    def import_eidoo(self, erc20_exist_name):
        logging.info("get eidoo")
        coin_names = self.get_eidoo_list()
        names = self.get_valid_name(coin_names)

        logging.info("filter eidoo {}".format(len(names)))
        names = self.filter_by_name(names, erc20_exist_name)
        logging.info("filter eidoo {}".format(len(names)))

        logging.info("search url")
        urls = []
        # for name in names:
        #     url = search_erc20(name)
        #     urls.append(url)
        with futures.ThreadPoolExecutor() as executor:
            res = executor.map(self.search_erc20, names)
            urls = list(res)
        return urls

    def import_escan(self, exist_addr):
        # may multiple page
        page_no = self.get_page_no()

        # get all token
        logging.info('get token list')
        hrefs = set()
        for page in range(page_no + 1):
            try:
                token_page_url = "{}?p={}".format(token_url, page)
                subset = self.get_token_url(token_page_url, exist_addr)
                hrefs.update(subset)
            except:
                break

        return hrefs

    def dump_solidity(self, url):
        try:
            name, address, solidity = self.get_token_info(url)
            filename = '{}.sol'.format(address)
            # filename = '{}.{}.sol'.format(name, address)
            # filename = regular_name(filename)
            with open('ICO/{}'.format(filename), 'w+') as fd:
                fd.write(solidity)
            logging.info("from {} get {}".format(url, name))
            res = {
                'address': address,
                'name': name
            }
            return res
        except Exception as e:
            logging.info("from {} failed".format(url, ))
            # traceback.print_exc()
        return None


def main(args):
    session = ICOCrawlSession()

    try:
        with open('ICO.json', 'r') as fd:
            config = json.load(fd)
    except:
        config = {
            'ERC20': [],
            'ERC721': [],
        }
    erc20_exist_addr = set([i['address'] for i in config['ERC20']])
    erc20_exist_name = set([i['name'] for i in config['ERC20']])

    report_list = []

    def do_dump(url):
        report = session.dump_solidity('{}'.format(url))
        if report:
            report_list.append(report)

    # get from eidoo
    if args.eidoo:
        # import data from eidoo
        eidoo_urls = session.import_eidoo(erc20_exist_name)
        for item in eidoo_urls:
            logging.info(item)
        eidoo_urls = session.filter_by_address(eidoo_urls, erc20_exist_addr)
        logging.info('get from eidoo')
        with futures.ThreadPoolExecutor() as executor:
            res = executor.map(do_dump, list(eidoo_urls))

    # get from escan
    if args.escan:
        escan_urls = session.import_escan(erc20_exist_addr)
        escan_urls = session.filter_by_address(escan_urls, erc20_exist_addr)
        logging.info('get from erc20')
        with futures.ThreadPoolExecutor() as executor:
            res = executor.map(do_dump, list(escan_urls))

    if args.value:
        urls = set()
        for i in args.value:
            i = i.lower()
            if i.startswith('0x'):
                urls.add('{}/{}'.format(address_url, i))
            elif i.startswith('http'):
                i = i.split('/').pop()
                urls.add('{}/{}'.format(address_url, i))
        with futures.ThreadPoolExecutor() as executor:
            res = executor.map(do_dump, list(urls))

    # dump
    with open('ICO.json', 'w') as fd:
        config['ERC20'] += report_list
        json.dump(config, fd, indent=4)
    logging.info('update with: {} ico'.format(len(report_list)))


def test_get_token():
    session = ICOCrawlSession()
    href = "/address/0xb64ef51c888972c908cfacf59b47c1afbc0ab8ac"
    res = session.get_token_info(href)


def test_fix_json():
    out = sh.ls('ICO').stdout.decode('utf-8')
    lines = str(out).split('\n')
    res = []
    for l in lines:
        if l.endswith('.sol'):
            item = l.split('.')
            addr = item[-2]
            name = '.'.join(item[:-2])
            res.append({'address': addr, 'name': name})
    return res


def test_fix_filename():
    out = sh.ls('ICO').stdout.decode('utf-8')
    lines = str(out).split('\n')
    res = []
    for l in lines:
        if l.startswith('0x'):
            continue
        if l.endswith('.sol'):
            item = l.split('.')
            addr = item[-2]
            name = '.'.join(item[:-2])
            res.append({'address': addr, 'name': name})
            sh.mv('ICO/{}'.format(l), 'ICO/{}.sol'.format(addr))

    exit()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-e", "--eidoo", help="use eidoo website",
                        action="store_true", dest="eidoo")
    parser.add_argument("-s", "--escan", help="use escan website",
                        action="store_true", dest="escan")
    parser.add_argument("-u", "--update", help="update local tmp data",
                        action="store", default=0, type=int, dest="update")
    parser.add_argument("-d", "--delay", help="process with delay",
                        action="store", default=1, type=int, dest="delay")
    parser.add_argument("value", nargs='*')
    args = parser.parse_args()

    update = args.update
    delay = args.delay

    if not args.value:
        args.escan = True

    main(args)
