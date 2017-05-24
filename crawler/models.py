import requests

import crawler.util as util


class WebPage:
    '''Representation of webpage.'''

    def __init__(self, url, load_page=True, params=None, **kwargs):
        self._url = util.normalize_url(url)
        self.loaded = False
        if load_page:
            self.reload(params=params, **kwargs)

    def __hash__(self):
        return hash(self._url)

    def __eq__(self, other):
        return self._url == other._url

    def __repr__(self):
        return "WebPage(url={!r}, load_page={!r})".format(
            self._url, bool(self.loaded)
        )

    @property
    def url(self):
        return self._url

    def reload(self, params=None, head_request=False, **kwargs):
        '''Reload webpage and updates links & emails.'''
        if head_request:
            self._response = requests.head(self._url, params=params, **kwargs)
        else:
            self._response = requests.get(self._url, params=params, **kwargs)
            self.loaded = True

    def __getattr__(self, attr):
        '''Redirects attributes getter to response.'''
        if "_response" in self.__dict__ and hasattr(self._response, attr):
            return getattr(self._response, attr)
        raise AttributeError("WebPage object has no attribute '%s', "
                             "try to reload the page." % attr)


class WebGraph:
    '''Representation of relation between webpages.'''
    
    def __init__(self):
        self.graph = dict()
        self.pages = set()

    def add_relation(self, p1, p2, directed=True):
        '''
        Add relation between pages to graph. Force using keyword parameters 
        to avoid mistakes.
        '''
        self.graph.setdefault(p1, set()).add(p2)
        if not directed:
            self.graph.setdefault(p2, set()).add(p1)
        else:
            if p2 not in self.graph: self.graph[p2] = set()

        self.pages.update((p1, p2))

    def find_nearest_neighbours(self, page, max_dist, with_dist=True):
        ''' 
        Searches for the neighbours of the page within defined distance. 
        Returns list of tuples (page, distance).
        '''

        # Ensure page is a WebPage.
        if not isinstance(page, WebPage):
            page = self._url2webpage(page)

        # Return None when page does not exist.
        if page not in self:
            return None    

        # Return empty list if no direct neightbours
        if page not in self.graph:  
            return []

        page2visit = set((page,))
        visited = set()
        dists = { page: 0 }
        neighbours = set()

        while page2visit:
            current = page2visit.pop()
            visited.add(current)

            current_dist = dists[current]
            for page in (self.graph[current] - visited):
                alt = current_dist + 1
                if alt <= max_dist:
                    neighbours.add(page)
                if alt < max_dist:
                    page2visit.add(page)
                if not page in dists or alt < dists[page]:
                    dists[page] = alt                            

        if with_dist:
            return [(page, dists[page]) for page in neighbours]
        else:
            return list(neighbours)


    def find_path(self, pstart, pend):
        '''
        Searches for the shorthest path between two pages. Returns tuple 
        containing consequtive pages in the path or None if there is not path.
        '''

        # Ensure pstart and pend are WebPage-s.
        if not isinstance(pstart, WebPage):
            pstart = self._url2webpage(pstart)
        if not isinstance(pend, WebPage):
            pend = self._url2webpage(pend)

        # Return None when one of the pages does not exist in the graph.
        if not pstart in self or not pend in self:
            return None

        # Return None when one of the pages has no connections
        if not pstart in self.graph or not pend in self.graph:
            return None

        # Test whether the pages are directly connected
        if pend in self.graph[pstart] or pstart in self.graph[pend]:
            return (pstart, pend)

        # Implementation of Dijkstra's algorithm
        not_visited = self.pages
        dists = { page: len(self)+1 for page in not_visited }
        dists[pstart] = 0
        prevs = { page: None for page in not_visited }

        while not_visited:
            min_dist = min(dists[item] for item in dists if item in not_visited)
            current = next(p for p in not_visited if dists[p] == min_dist)
            not_visited -= set((current,))
        
            # Shortes path has been found            
            if current == pend:
                break

            current_dist = dists[current]
            for page in self.graph[current]:
                alt = current_dist + 1
                if alt < dists[page]:
                    dists[page] = alt
                    prevs[page] = current

        path = list()
        target = pend
        while prevs[target]:
            path.append(target)
            target = prevs[target]
        else:
            if path: path.append(target)

        return tuple(reversed(path)) or None


    def get_page(self, url, create_new=True):
        '''
        Returns page with given url or creates new one if there is no page 
        with the url.
        '''
        if isinstance(url, WebPage):
            url = url.url
        url = util.normalize_url(url)

        for page in self.pages:
            if page.url == url:
                return page
        else:
            if create_new:
                return WebPage(url=url, load_page=False)

        # return self.pages.get(
        #     WebPage(url, load_page=False), 
        #     (create_new and WebPage(url=url, load_page=False) or None)
        # )

    def add_page(self, obj, parent=None):
        '''
        Adds page to graph. Accepts WebPage or url(string).
        '''
        if not isinstance(obj, WebPage):
            obj = self._url2webpage(obj)
        self.pages.add(obj)
        if parent:
            self.add_relation(parent, obj)
        return obj

    def _url2webpage(self, url, load_page=False):
        return WebPage(url=util.normalize_url(url), load_page=load_page)

    def __contains__(self, page):
        if not isinstance(page, WebPage):
            page = self._url2webpage(page)
        return page in self.pages

    def __iter__(self):
        return iter(self.pages)

    def __getitem__(self, page):
        return self.graph[page]

    def __len__(self):
        return len(self.pages)