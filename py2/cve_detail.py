import requests
import bs4
import re

"https://www.cvedetails.com/product-search.php?vendor_id=0&search=openssl"

def get_cve_lib():
    prefix = "https://www.cvedetails.com/vendor/firstchar-L/"
    suffix = "/?sha=3cae7a4e749f90be1a19651d1d67f209653e4dfe&trc=615&order=1"
    urls = ["{}{}{}".format(prefix, i, suffix) for i in range(1, 8)]
    for url in urls:
        res = requests.get(url)
        soup = bs4.BeautifulSoup(res.text, "html.parser")

        form = soup.find('form', attrs={'action': "/vendor-match.php", 'method': "get"})
        # <form action="/vendor-match.php" method="get">
        table = form.find('table', attrs={'class': 'listtable'})
        # <table class="listtable">
        target = table.find_all('a', text=re.compile("(l|L).*"))
        for a in target:
            name = a.text
            print(name.strip())


def get_cve_info():
    urls = [
        "https://www.cvedetails.com/vulnerability-list/vendor_id-217/product_id-383/version_id-126011/Openssl-Openssl-1.0.1.html",
        # "https://www.cvedetails.com/vulnerability-list.php?vendor_id=217&product_id=383&version_id=126011&page=2&hasexp=0&opdos=0&opec=0&opov=0&opcsrf=0&opgpriv=0&opsqli=0&opxss=0&opdirt=0&opmemc=0&ophttprs=0&opbyp=0&opfileinc=0&opginf=0&cvssscoremin=0&cvssscoremax=0&year=0&month=0&cweid=0&order=1&trc=64&sha=7a24062fce0551418f0aa1016d167bdbeaffe316"

    ]
    for url in urls:
        res = requests.get(url)
        soup = bs4.BeautifulSoup(res.text, "html.parser")

        contentdiv = soup.find('div', id='searchresults')
        target = contentdiv.find_all('a', href=re.compile("/cve/CVE-[0-9.-]+/"))
        for a in target:
            cve = a.get('href')
            print(cve)


def main():
    get_cve_lib()


if __name__ == '__main__':
    main()
