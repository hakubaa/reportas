from concurrent import futures
import urllib.parse as urlparse
import requests
import pdb
import csv
import operator
from functools import reduce

from requests.exceptions import RequestException

from crawler.models import  WebPage, WebGraph
from crawler.util import fmap, find_urls, update_netloc


class WebCrawler:

    def __init__(self, max_workers=1, webgraph=None, callback=None):
        self.webgraph = webgraph or WebGraph()
        self.max_workers = max_workers
        self.external_filters = []
        self.callback = callback
        self.visited = set() # list of visisted pages

    def add_filter(self, filter):
        self.external_filters.append(filter)

    def _filter_within_domain(self, root_url):
        def _filter(page):
            _, root_netloc, *_ = urlparse.urlsplit(root_url)
            _, netloc, *_ = urlparse.urlsplit(page.url)
            if root_netloc == netloc:
                return True
            else:
                return False
        return _filter

    def _search_urls(self, page):
        '''
        Search webpage for emails and urls. Returns dict with found items.
        '''
        if not page.loaded:
            raise ValueError("empty WebPage object, reload required")

        content_type = page.headers.get("Content-Type", None)
        if not (content_type and content_type.startswith("text")):
            return list()

        urls = [update_netloc(page.url, url) for url in find_urls(page)]
        return urls

    def _update_internals(self, page):
        '''Search webpage and updage webgraph.'''
        urls = self._search_urls(page)
        for url in urls:
            self.webgraph.add_page(url, parent=page)

    @property
    def emails(self):
        return reduce(operator.or_, self._emails.values(), set())

    def __getitem__(self, page):
        return self._emails[page]

    def _submit_worker(self, page, executor):
        future = executor.submit(page.reload)
        if self.callback:
            future.add_done_callback(lambda fn: self.callback(fn.result()))
        return future

    def search(self, root_page, max_depth, within_domain=True):

        # Set filters
        filters = self.external_filters
        if within_domain:
            filters.append(self._filter_within_domain(root_page.url))

        workers = dict()

        with futures.ThreadPoolExecutor(self.max_workers) as executor:
            workers[root_page] = self._submit_worker(root_page, executor)
            try:
                while workers:
                    # Collect pages
                    for page, future in list(workers.items()):
                        if future.done():
                            self._update_internals(page)
                            self.visited.add(page)
                            del workers[page]

                    # Check for new pages to visist
                    pages2visit = self.webgraph.find_nearest_neighbours(
                        root_page, max_depth, with_dist=False
                    )

                    if pages2visit:
                        # Apply filters
                        pages2visit = (
                            set(pages2visit) - self.visited - set(workers)
                        )
                        pages2visit = (page for page in pages2visit 
                                           if all(fmap(page, *filters)))
                        for page in pages2visit:
                            workers[page] = self._submit_worker(page, executor)

            except KeyboardInterrupt:
                executor.shutdown()
                for page, future in workers.items():
                    if future.done():
                        self._update_internals(page)