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
import warnings

import nltk
import pandas as pd
import numpy as np

from parser.nlp import NGram, find_ngrams
import parser.util as util


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

    def __init__(self, text, columns_number=None, note_presence=None):
        self.columns_number = columns_number
        self.note_presence = note_presence
        self.rows = self._preprocess_labels(self._extract_rows(text))

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        try:
            return self.rows[index]
        except IndexError:
            raise IndexError("row number out of range")

    def __iter__(self):
        return iter(self.rows)

    def _split_row_into_fields(self, row):
        '''Split text into separate fields.'''
        return list(filter( # use filter to remove empty fields ('')
            bool, re.split(ASCITable.re_fields_separators, row)
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

    def _preprocess_labels(self, input_rows):
        '''Row: label (note) number_1 number_2 ... number_n'''

        rows = list(input_rows)

        # 1. Identify and fix column with label
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

        # Get rid of leading numbers
        # Comming Soon !!!
                
        # 2. Convert numbers, keep labels, ignore optional parts
        # if self.columns_number:
        #     fields_in_row = self.columns_number
        # else:
        #     fields_in_row = Counter(map(len, rows)).most_common(1)[0][0] - 1

        # std_rows = list()
        # for row in rows:
        #     std_rows.append(row[0:1] + [ util.convert_to_number(item) 
        #                     for item in row[-fields_in_row:] ])

        return rows

    def _identify_records(self, rows, recspec, min_csim=0.9):
        stack = list()
        for index, row in enumerate(rows):
            # Check for presence of label and find the most similar label
            # in specification.
            label_tokens = find_ngrams(row[0], n=1)
            if label_tokens:
                csims = list(map(
                    lambda spec: (
                        spec["id"], 
                        cos_similarity(spec["ngrams"], label_tokens)
                    ), 
                    recspec
                ))

            # Check for presence of numbers in the row
            row_numbers_count = sum(map(is_number, row))

            if label_tokens and row_numbers_count: # full row
                numbers = row[-row_numbers_count:]
                stack.append((label_tokens, numbers, csims, (index,)))
            elif label_tokens:
                try:
                    s_label, s_numbers, s_csims, s_index = stack.pop()
                except IndexError:
                    stack.append((label_tokens, None, csims, (index,)))
                else:
                    # import pdb; pdb.set_trace()
                    ext_label = label_tokens + s_label
                    ext_csims = list(map(
                        lambda spec: (
                            spec["id"], 
                            cos_similarity(spec["ngrams"], ext_label)
                        ), 
                        recspec
                    ))

                    max_ext_csims = max(ext_csims, key=operator.itemgetter(1))[1]
                    max_s_csims = max(s_csims, key=operator.itemgetter(1))[1]
                    max_csims = max(csims, key=operator.itemgetter(1))[1]

                    if max_ext_csims > max_s_csims and max_ext_csims > max_csims:
                        stack.append((ext_label, s_numbers, ext_csims, 
                                      s_index + (index,)))
                    else:
                        stack.append((s_label, s_numbers, s_csims, s_index))
                        stack.append((label_tokens, None, csims, (index,)))
            elif row_numbers_count:
                numbers = row[-row_numbers_count:] 
                try:
                    s_label, s_numbers, s_csims, s_index = stack.pop()
                except IndexError:
                    # stack.append((None, numbers, None))
                    pass
                else:
                    if s_label and not s_numbers:
                        stack.append((s_label, numbers, s_csims, 
                                      s_index + (index,)))
                    else:
                        pass
                        # stack.append((None, numbers, None))
            else:
                continue

        # Reduce stack
        identified_records = list()
        for label, numbers, csims, rows_indices in stack:
            max_csim = max(csims, key=operator.itemgetter(1))[1]
            if max_csim > min_csim:
                spec_id = tuple(id for id, csim in csims 
                                   if abs(csim - max_csim) < 1e-3)
                identified_records.append(
                    (spec_id, numbers, rows_indices)
                )

        return identified_records

                

class SelfSearchingPage:

    min_probe_rate = 0.5 # coefficient for filtiring adjecant pages to page
    # with highest probability

    def __init__(self, modelpath, storage_name = None, use_number_ngram=True, 
                 use_page_ngram=True):
        self.storage_name = storage_name
        self.use_number_ngram = use_number_ngram
        self.use_page_ngram = use_page_ngram
        try:
            with open(modelpath, "rb") as f:
                self.model = pickle.load(f)
        except FileNotFoundError:
            warnings.warn("No such file or directory: '{}'".format(modelpath))
            self.model = None

    def _extract_ngrams(self, text, n=2):
        freq = Counter(find_ngrams(text, n))
        if self.use_number_ngram:
            freq[NGram("fake#number")] = len(util.find_numbers(text))
        return freq

    def _select_ngrams(self, text_ngrams):
        return [text_ngrams[ngram] for ngram in self.model["ngrams"]]

    def __get__(self, doc, owner):
        # when the model was not load in init, inform user that sth went
        # wrong and raise attribut error
        if not self.model:
            cls_name = doc.__class__.__name__
            raise AttributeError("'{}' object has no attribute '{}'".format(
                cls_name, self.storage_name)
            )

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
    net_and_loss = SelfSearchingPage("parser/cls/nls.pkl", "net_and_loss")
    balance = SelfSearchingPage("parser/cls/balance.pkl", "balance")
    cash_flows = SelfSearchingPage("parser/cls/cfs.pkl", "cash_flows")

    def __init__(self, *args, consolidated=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.consolidated = consolidated