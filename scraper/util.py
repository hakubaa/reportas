import re
import urllib.parse as urlparse
import imp
import importlib
import sys
import inspect
import ctypes
import itertools
from concurrent import futures
from datetime import datetime

import requests
from bs4 import BeautifulSoup


RE_EMAIL = r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)"
RE_URL = r"(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))"\
         r"([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?"


def find_with_re(text, pattern):
    '''Return an iterator over all non-overlapping matches in the text.'''
    rpattern = re.compile(pattern)
    return (match.group() for match in rpattern.finditer(text))


def find_with_bs(soup, tag, attr=None):
    '''
    Return an iterator over all non-overlapping tags/attr in the page. When attr
    is not null return the value of the attr, otherwise the value of the tag.
    '''
    tags = soup.find_all(tag)
    return ((not attr and tag) or tag.get(attr, None) for tag in tags)


def filter_with_re(iterable, pattern=None):
    if not pattern:
        return iterable
    rpattern = re.compile(pattern)
    return (item for item in iterable if rpattern.match(item))


def url_fix(s, charset='utf-8'):
    """Fix url."""
    if isinstance(s, bytes):
        s = s.decode(charset, 'ignore')
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(s)
    path = urlparse.quote(path, '/%')
    qs = urlparse.quote_plus(qs, ':&=')
    return urlparse.urlunsplit((scheme, netloc, path, qs, anchor))


def normalize_url(url, charset="utf-8"):
    '''Normalize url. Get rid of query and anchor.'''
    if isinstance(url, bytes):
        url = url.decode(charset, errors="ignore")
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(url)
    path = urlparse.quote(path, "/%")
    if path == "": path = "/"
    return urlparse.urlunsplit((scheme, netloc, path, qs, None))


def fmap(item, *args):
    '''Applies each func in args to item, yielding the result.'''
    return (f(item) for f in args)


def find_urls(page, normalize=True):
    '''
    Extracts all the URLs found within a page.
    '''
    content = page.content
    content = content.decode(getattr(page, "encoding", "utf-8"), 
                             errors="ignore")

    soup = BeautifulSoup(content, "html.parser")
    urls = list(set(itertools.chain(
        find_with_re(str(soup), RE_URL),
        filter(
            lambda item: item and not item.startswith("mailto:"), 
            find_with_bs(soup, "a", "href")
        ))))
    if normalize:
        urls = [normalize_url(url) for url in urls]
    return urls


def find_emails(page):
    '''
    Extracts all the emails found within a page.
    '''
    content = page.content
    content = content.decode(getattr(page, "encoding", "utf-8"), 
                             errors="ignore")

    soup = BeautifulSoup(content, "html.parser")
    emails = list(set(find_with_re(str(soup), RE_EMAIL)))
    return emails


def update_netloc(root_url, url):
    '''Convert relative hyperlinks to absolute hyperlinks.'''
    root_scheme, root_netloc, *_ = urlparse.urlsplit(root_url)
    scheme, netloc, path, qs, anchor = urlparse.urlsplit(url_fix(url))
    if not netloc:
        url = urlparse.urlunsplit((
            root_scheme, root_netloc, path, qs, anchor
        ))
    return url


keys_mapper = {
    "Na giełdzie od": "debut",
    "Emitent": "fullname",
    "Nazwa giełdowa": "name",
    "Nazwa": "name",
    "Nazwa pełna": "fullname",
    "Adres siedziby": "address",
    "Województwo": "district",
    "Numer telefonu": "telephone",
    "Numer faksu": "fax",
    "Strona www": "webpage",
    "E-mail": "email",
    "Branża": "sector",
    "Ticker": "ticker",
    "Liczba wyemitowanych akcji": "shares",
    "Prezes Zarządu": "charmain",
    "Wartość rynkowa (mln zł)": "markevalue",
    "Skrót": "ticker"
}


def get_data_from_gpw(ISIN, start="infoTab"):
    '''Download data from gpw about selected company represented by ISIN.'''
    page = requests.post(
        "https://www.gpw.pl/ajaxindex.php", 
        params = {
            "action": "GPWListaSp",
            "start": start,
            "gls_isin": ISIN,
            "lang": "PL"
        }
    )

    soup = BeautifulSoup(page.content.decode("utf-8"), "lxml")
    rows = soup.find_all("tr")

    data = list()
    for row in rows:
        values = list(
            re.sub("(\\n|\\t|\\xa0|:$)", "", ele.text.strip()) 
            for ele in row.find_all(["th", "td"])
        )
        values[0] = keys_mapper.get(values[0], values[0])
        data.append(tuple(values))

    return dict(data)


def get_list_of_companies():
    '''Download list of companies from infostrefa.pl'''
    page = requests.get(
        "http://infostrefa.com/infostrefa/pl/spolki?market=mainMarket"
    )
    soup = BeautifulSoup(page.content, "html.parser")

    # Locate table with companies (can change in the future) and extract data
    table_body = soup.select("div#companiesList table")[0]
    rows = table_body.find_all("tr")

    headers = list(map(
        lambda x: keys_mapper.get(x.text.strip(), x.text.strip()), 
        rows[0].find_all("td")
    ))
    companies = []
    for row in rows[1:]:
        values = [ele.text.strip() for ele in row.find_all("td")]
        companies.append(dict(zip(headers, values)))

    return companies


def get_companies(verbose=True, tickers=None, max_workers=3):
    '''Update companies in db. Scrape data from the Internet.'''

    ## Get list of companies listed on WSE
    companies = get_list_of_companies()
    if tickers:
        tickers = [ ticker.upper() for ticker in tickers ]
        companies = filter(
            lambda item: item["ticker"].upper() in tickers, companies
        )

    ## Load more info from gpw.pl
    cobjs = list()
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        to_do = []
        for company in companies:
            future = executor.submit(get_data_from_gpw, company["ISIN"])
            to_do.append(future)
            if verbose:
                print("Scheduled for {}: {}".format(company["ISIN"], future))

        for future in futures.as_completed(to_do):
            res = future.result()
            data = {  # 3.5 required
                key: value for key, value in {**company, **res}.items()
            }
            if "debut" in data:
                month, year = data["debut"].split(".")
                data["debut"] = datetime(int(year), int(month), 1)

            cobjs.append(data)
            if verbose: 
                print("{} result: {}".format(future, data["ISIN"]))

    return cobjs