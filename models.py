# -*- coding: utf-8 -*

from functools import reduce
from collections import Counter
import operator
import itertools
import reprlib
import numbers
import pickle
import re
from enum import Enum

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
        text, errors = util.pdftotext(
            docpath, layout=True, first_page=first_page, last_page=last_page
        ) 
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


class ASCITable:

    re_fields_separators = re.compile(r"(?:\s)*(?:\||\s{2,}|\t|;)(?:\s)*")
    re_rows_separators = re.compile(r"\n")
    re_alphabetic_chars = re.compile("[A-Za-zżźćńółęąśŻŹĆĄŚĘŁÓŃ]")

    def __init__(self, text=None):
        self.rows = self._standardize_rows(self._extract_rows(text))

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        try:
            return self.rows[index]
        except IndexError:
            raise IndexError("row number out of range")

    def __iter__(self):
        return iter(self.rows)

    def _split_row_into_fields(self, text):
        '''Split text into separate fields.'''
        return list(filter( # use filter to remove empty fields ('')
            bool, re.split(ASCITable.re_fields_separators, text)
        ))

    def _split_text_into_rows(self, text):
        '''Split text into rows. Remove empty rows.'''
        rows = re.split(ASCITable.re_rows_separators, text)
        rows = [ row for row in rows if not row.isspace() ]
        return rows

    def _extract_rows(self, text):
        '''Create simple table. Each row as separate list of fields.'''
        table = [self._split_row_into_fields(row) 
                 for row in self._split_text_into_rows(text)]
        table = [ row for row in table if row ] # remove empty rows
        return table

    def _standardize_rows(self, input_rows):
        '''Row: label (note) number_1 number_2 ... number_n'''

        # 1. Keep only rows with at least one number
        rows = [ row for row in input_rows if any(map(util.isnumber, row)) ]
        if not rows: # no row with at least one number
            return []

        # 2. Remove rows with not enough fields
        mode_of_fields_in_row = Counter(map(len, rows)).most_common(1)[0][0]

        rows = list(filter(lambda row: len(row) >= mode_of_fields_in_row, rows))

        # 3. Identify and fix column with label
        fields_length_by_rows = list(map(lambda row: list(map(
            lambda field: 
                len(re.findall(ASCITable.re_alphabetic_chars, field)), 
            row
        )), rows))

        for index, row in enumerate(fields_length_by_rows):
            field_with_max_chars = np.array(row).argmax()
            if field_with_max_chars > 0:
                rows[index][0:(field_with_max_chars+1)] = [
                    ' '.join(rows[index][0:(field_with_max_chars+1)])
                ]
                
        # 4. Convert numbers, keep labels, ignore optional parts
        mode_of_fields_in_row = Counter(map(len, rows)).most_common(1)[0][0]

        std_rows = list()
        for row in rows:
            std_rows.append(row[0:1] + [ util.convert_to_number(item) 
                            for item in row[-(mode_of_fields_in_row-1):] ])

        return std_rows


class SelfSearchingPage:

    min_probe_rate = 0.5 # coefficient for filtiring adjecant pages to page
    # with highest probability

    def __init__(self, modelpath, storage_name = None, use_number_ngram=True, 
                 use_page_ngram=True):
        self.storage_name = storage_name
        self.use_number_ngram = use_number_ngram
        self.use_page_ngram = use_page_ngram
        with open(modelpath, "rb") as f:
            self.model = pickle.load(f)

    def _extract_ngrams(self, text, n=2):
        freq = Counter(util.find_ngrams(text, n))
        if self.use_number_ngram:
            freq[NGram("fake#number")] = len(util.find_numbers(text))
        return freq

    def _select_ngrams(self, text_ngrams):
        return [text_ngrams[ngram] for ngram in self.model["ngrams"]]

    def __get__(self, doc, owner):
        ngrams_by_pages = list(map(self._extract_ngrams, doc))
        if self.use_page_ngram: # Append fake page ngram for every page
            for index, ngrams in enumerate(ngrams_by_pages):
                ngrams[NGram("fake#page")] = index / len(doc)
        ngrams_freq = map(self._select_ngrams, ngrams_by_pages)
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

        doc.__dict__[self.storage_name] = page_numbers

        return page_numbers
 

class FinancialReport(Document):
    net_and_loss = SelfSearchingPage("smodels/nls.pkl", "net_and_loss")
    balance = SelfSearchingPage("smodels/balance.pkl", "balance")
    cash_flows = SelfSearchingPage("smodels/cfs.pkl", "cash_flows")

    def __init__(self, *args, consolidated=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.consolidated = consolidated