# -*- coding: utf-8 -*

from functools import reduce
from collections import Counter
import operator
import itertools
import reprlib
import numbers
import pickle

import nltk
import pandas as pd
import numpy as np

import util


# polish stop words (source: wikipedia)
STOP_WORDS = set("a, aby, ach, acz, aczkolwiek, aj, albo, ale, ależ, ani, aż, bardziej, bardzo, bo, bowiem, by, byli, bynajmniej, być, był, była, było, były, będzie, będą, cali, cała, cały, ci, cię, ciebie, co, cokolwiek, coś, czasami, czasem, czemu, czy, czyli, daleko, dla, dlaczego, dlatego, do, dobrze, dokąd, dość, dużo, dwa, dwaj, dwie, dwoje, dziś, dzisiaj, gdy, gdyby, gdyż, gdzie, gdziekolwiek, gdzieś, i, ich, ile, im, inna, inne, inny, innych, iż, ja, ją, jak, jakaś, jakby, jaki, jakichś, jakie, jakiś, jakiż, jakkolwiek, jako, jakoś, je, jeden, jedna, jedno, jednak, jednakże, jego, jej, jemu, jest, jestem, jeszcze, jeśli, jeżeli, już, ją, każdy, kiedy, kilka, kimś, kto, ktokolwiek, ktoś, która, które, którego, której, który, których, którym, którzy, ku, lat, lecz, lub, ma, mają, mało, mam, mi, mimo, między, mną, mnie, mogą, moi, moim, moja, moje, może, możliwe, można, mój, mu, musi, my, na, nad, nam, nami, nas, nasi, nasz, nasza, nasze, naszego, naszych, natomiast, natychmiast, nawet, nią, nic, nich, nie, niech, niego, niej, niemu, nigdy, nim, nimi, niż, no, o, obok, od, około, on, ona, one, oni, ono, oraz, oto, owszem, pan, pana, pani, po, pod, podczas, pomimo, ponad, ponieważ, powinien, powinna, powinni, powinno, poza, prawie, przecież, przed, przede, przedtem, przez, przy, roku, również, sama, są, się, skąd, sobie, sobą, sposób, swoje, ta, tak, taka, taki, takie, także, tam, te, tego, tej, temu, ten, teraz, też, to, tobą, tobie, toteż, trzeba, tu, tutaj, twoi, twoim, twoja, twoje, twym, twój, ty, tych, tylko, tym, u, w, wam, wami, was, wasz, wasza, wasze, we, według, wiele, wielu, więc, więcej, wszyscy, wszystkich, wszystkie, wszystkim, wszystko, wtedy, wy, właśnie, z, za, zapewne, zawsze, ze, zł, znowu, znów, został, żaden, żadna, żadne, żadnych, że, żeby, pln, '000, ..., .., -, +".replace(" ", "").split(","))


class NGram:

    def __init__(self, *args):
        if not args:
            raise TypeError("init expected at least 1 arguments, got 0")
        if not all(isinstance(arg, str) for arg in args):
            raise TypeError("init expected str arguments")
        self._tokens = list(args)

    def __repr__(self):
        return "NGram('{}')".format("', '".join(self._tokens))

    def __hash__(self):
        hashes = (hash(token + str(index)) for index, token in enumerate(self))
        return reduce(operator.xor, hashes)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        return tuple(self) == tuple(other)

    def __len__(self):
        return len(self._tokens)

    def __getitem__(self, index):
        cls = type(self)
        if isinstance(index, slice):
            return cls(*self._tokens[index])
        elif isinstance(index, numbers.Integral):
            return self._tokens[index]
        else:
            msg = "{cls.__name__} indices must be integers"
            raise TypeError(msg.format(cls=cls))

    def __iter__(self):
        return iter(self._tokens)


class Document:

    verbose = False

    def __init__(self, docpath, pgbrk='\x0c', encoding="UTF-8",
                 first_page=None, last_page=None):
        if Document.verbose:
            print("Loading document '{}' ... ".format(docpath), end="")
        self.docpath = docpath
        text, errors = util.pdftotext(docpath, layout=True, first_page=first_page,
                                 last_page=last_page) 
        if errors:
            raise RuntimeError("pdftotext returned exit code: %r", errors)
        self.raw_text = str(text, encoding)
        self.pages = self.raw_text.split(pgbrk)
        if Document.verbose:
            print("DONE")

    def __len__(self):
        return len(self.pages)

    def __hash__(self):
        return hash(self.raw_text)

    def __eq__(self, other):
        if len(self.raw_text) != len(other.raw_text):
            return False
        return self.raw_text == other.raw_text

    def __iter__(self):
        return iter(self.pages)

    def __getitem__(self, index):
        try:
            return self.pages[index]
        except IndexError:
            raise IndexError("page number out of range")

    def __repr__(self):
        return "{}('{}')".format(self.__class__.__name__, self.docpath)


class SelfSearchingPage:

    min_probe_rate = 0.5 # coefficient for filtiring adjecant pages to page
    # with highest probability

    def __init__(self, attrname, modelpath, use_number_ngram=True, 
                 use_page_ngram=True):
        self.attrname = attrname
        self.use_number_ngram = use_number_ngram
        self.use_page_ngram = use_page_ngram
        with open(modelpath, "rb") as f:
            self.model = pickle.load(f)

    def _extract_ngrams(self, text, n=2):
        freq = Counter(util.find_ngrams(text, n))
        if self.use_number_ngram:
            freq[NGram("fake#number")] = len(util.find_numbers(text))
        return freq

    def _select_and_order_ngrams(self, text_ngrams):
        return [text_ngrams[ngram] for ngram in self.model["ngrams"]]

    def __get__(self, doc, owner):
        ngrams_by_pages = list(map(self._extract_ngrams, doc))
        if self.use_page_ngram: # Append fake page ngram for every page
            for index, ngrams in enumerate(ngrams_by_pages):
                ngrams[NGram("fake#page")] = index / len(doc)
        ngrams_freq = map(self._select_and_order_ngrams, ngrams_by_pages)
        prob_by_pages = self.model["clf"].predict_proba(
            np.asarray(list(ngrams_freq))
        )[:,1]

        # Standalone vs consolidated financial statements are often included
        # in the same report. The balance sheet, net and loss account and 
        # cash flows statements are very similar for standalone and 
        # consolidated statements. Choose the correct one on the base of 
        # financial report's type.
        if getattr(doc, "consolidated", False):
            for index, ngrams_page in enumerate(ngrams_by_pages):
                if NGram("jednostkowe", "sprawozdanie") in ngrams_page \
                   or NGram("finansowe", "jednostkowe") in ngrams_page:
                    prob_by_pages[index] = 0

        page_with_max_prob = prob_by_pages.argmax()
        max_prob = prob_by_pages.max()

        preceding_pages = len(list(itertools.takewhile(
            lambda prob: prob > max_prob * SelfSearchingPage.min_probe_rate,
            reversed(prob_by_pages[0:page_with_max_prob])
        )))

        suceeding_pages = len(list(itertools.takewhile(
            lambda prob: prob > max_prob * SelfSearchingPage.min_probe_rate, 
            prob_by_pages[(page_with_max_prob + 1):]
        )))

        page_numbers = list(range(page_with_max_prob - preceding_pages,
                                  page_with_max_prob + 1 + suceeding_pages))

        doc.__dict__[self.attrname] = page_numbers

        return page_numbers


class FinancialReport(Document):
    net_and_loss = SelfSearchingPage("net_and_loss", "smodels/nls.pkl")
    balance = SelfSearchingPage("balance", "smodels/balance.pkl")
    cash_flows = SelfSearchingPage("cash_flows", "smodels/cfs.pkl")

    def __init__(self, *args, consolidated=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.consolidated = consolidated