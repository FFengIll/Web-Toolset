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
import re

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
    def filter_by_address(addr_set, exist_addr):
        logging.debug("possible ref no:{}".format(len(addr_set)))

        new_addr_set = set()
        for addr in addr_set:
            try:
                if addr in exist_addr:
                    continue
                else:
                    new_addr_set.add(addr)
            except:
                pass

        logging.debug("filtered ref no:{}".format(len(new_addr_set)))
        return new_addr_set

    def get_token_info(self, addr):
        url = self.get_url(addr)
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
        if info_a is None:
            info_a = summary_div.find('div:nth-child(1) > table > thead > tr > th > font', first=True)

        name = info_a.text

        # never keep any space char
        return name.strip(), addr.strip(), solidity.strip()

    def get_url(self, addr):
        return '{}/{}'.format(address_url, addr)

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
                logging.info(url)
                res = address.lower()
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

        logging.info("search address")
        with futures.ThreadPoolExecutor() as executor:
            addr_set = []
            for addr in executor.map(self.search_erc20, names):
                addr_set.append(addr)
        return addr_set

    def import_escan(self, exist_addr):
        addr_set = set()

        # may multiple page
        page_no = self.get_page_no()

        # get all token
        logging.info('get token list')
        for page in range(page_no + 1):
            try:
                token_page_url = "{}?p={}".format(token_url, page)
                r = self.get(token_page_url)
                table = r.html.find(
                    "#ContentPlaceHolder1_divresult > table tbody", first=True)
                links = table.find("a[href]")
                for item in links:
                    href = item.attrs['href']
                    addr = href.split('/').pop()
                    addr = addr.lower()

                    if addr not in exist_addr:
                        addr_set.add(addr)
            except:
                logging.error('import escan error!')
                break

        return addr_set

    def dump_event(self, addr, description):
        try:
            name, addr, solidity = self.get_token_info(addr)

            filename = '{}.sol'.format(addr)

            with open('event/{}'.format(filename), 'w+') as fd:
                fd.write(solidity)
            res = {
                'address': addr,
                'name': name,
                'description': description
            }
            return res
        except Exception as e:
            # logging.info("from {} failed".format(url, ))
            traceback.print_exc()
        return None

    def dump_ico(self, addr):
        try:
            name, address, solidity = self.get_token_info(addr)
            filename = '{}.sol'.format(address)
            # filename = '{}.{}.sol'.format(name, address)
            # filename = regular_name(filename)
            with open('ICO/{}'.format(filename), 'w+') as fd:
                fd.write(solidity)
            logging.info("from {} get {}".format(addr, name))
            res = {
                'address': address,
                'name': name
            }
            return res
        except Exception as e:
            logging.info("from {} failed".format(addr, ))
            # traceback.print_exc()
        return None


def main(args):
    session = ICOCrawlSession()

    if args.event:
        description = input("input the description: ")
        # description = 'Parity Bug (Wallet)'
        # crawl an event

        url = args.event
        pattern_addr = re.compile(r'0x[0-9a-f]+')
        match = pattern_addr.findall(url)
        if match:
            addr = match.pop().lower()
            logging.info('address: {}'.format(addr))
        else:
            logging.error('address error')
            return False

        res = session.dump_event(addr, description)
        if res:
            try:
                with open('event.json', 'r') as fd:
                    exists = json.load(fd)
            except:
                exists = {
                    'contract': [],
                }

            # erc20_exist_addr = set([i['address'] for i in exists['ERC20']])
            # erc20_exist_name = set([i['name'] for i in exists['ERC20']])

            # dump
            with open('event.json', 'w') as fd:
                exists['contract'].append(res)
                json.dump(exists, fd, indent=4)
        return True

    try:
        with open('erc20.json', 'r') as fd:
            exists = json.load(fd)
    except:
        exists = {
            'data': []
        }
    erc20_exist_addr = set([i['address'].lower() for i in exists['data']])
    erc20_exist_name = set([i['name'].lower() for i in exists['data']])

    report_list = []

    # get from eidoo
    if args.eidoo:
        # import data from eidoo
        eidoo_addr_set = session.import_eidoo(erc20_exist_name)
        for item in eidoo_addr_set:
            logging.info(item)

        eidoo_addr_set = session.filter_by_address(eidoo_addr_set, erc20_exist_addr)
        logging.info('get from eidoo')
        with futures.ThreadPoolExecutor() as executor:
            for res in executor.map(lambda addr: session.dump_ico(addr), list(eidoo_addr_set)):
                if res:
                    report_list.append(res)

    # get from escan
    if args.escan:
        escan_addr_set = session.import_escan(erc20_exist_addr)
        escan_addr_set = session.filter_by_address(escan_addr_set, erc20_exist_addr)
        logging.info('get from escan erc20')
        with futures.ThreadPoolExecutor() as executor:
            for res in executor.map(lambda addr: session.dump_ico(addr), list(escan_addr_set)):
                if res:
                    report_list.append(res)

    if args.ico:
        addr_set = set()
        for url in args.ico:
            pattern_addr = re.compile(r'0x[0-9a-f]+')
            match = pattern_addr.findall(url)
            if match:
                addr = match.pop().lower()
                addr_set.add(addr)

                logging.info('address: {}'.format(addr))
            else:
                logging.error('address error: {}'.format(url))
                continue

    # dump
    with open('erc20.json', 'w') as fd:
        exists['data'] += report_list
        # for item in exists['ERC20']:
        #     item['address']=item['address'].lower()
        json.dump(exists, fd, indent=4)
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
    parser.add_argument("-t", "--test", help="test mode, no file change",
                        action="store_true", dest="test")
    parser.add_argument("--event", help="process with delay",
                        action="store", default=None, type=str, dest="event")
    parser.add_argument("-i", "--ico", help="give an ico address",
                        action="store", default=None, type=str, dest="ico")
    parser.add_argument("value", nargs='*')
    args = parser.parse_args()

    update = args.update
    delay = args.delay

    if not args.value:
        args.escan = True

    main(args)
