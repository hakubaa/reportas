import re
import urllib.parse as urlparse
import imp
import importlib
import sys
import inspect
import ctypes
import itertools

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