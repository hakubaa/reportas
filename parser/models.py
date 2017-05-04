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

from parser.nlp import NGram, find_ngrams, cos_similarity
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
        # if remove_non_ascii:
        #     self.raw_text = util.remove_non_ascii(self.raw_text)
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

    min_probe_rate = 0.25 # coefficient for filtiring adjecant pages to page
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
                if any("jednostkowe" in ngram or "jednostkowy" in ngram 
                       for ngram in ngrams_page):
                    # decrease the probabilty
                    prob_by_pages[index] = prob_by_pages[index] * 0.5

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


class RecordsExtractor:

    re_fields_separators = re.compile(r"(?:\s)*(?:\||\s{2,}|\t|;)(?:\s)*")
    re_rows_separators = re.compile(r"\n")
    re_alphabetic_chars = re.compile(r"[A-Za-zżźćńółęąśŻŹĆĄŚĘŁÓŃ]")
    re_leading_number = re.compile(
        r"^(?:Nota)?(?:\s)*([A-Za-z]|(\d+)(?:\.\d+)*|(M{0,4}(CM|CD|D?C{0,3})"
        r"(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})))(\.|\)| )(?:\s)*"
    ) 

    def __init__(self, text, recspec, require_numbers=True, 
                 remove_non_ascii=True, min_csim=0.85, fix_white_spaces=True,
                 voc=None):
        self.voc = voc # used by _fix_white_spaces
        if remove_non_ascii:
            text = util.remove_non_ascii(text)
        temp_rows = self._extract_rows(text)
        self.input_rows = self._preprocess_labels(temp_rows)
        if fix_white_spaces:
             self.input_rows = self._fix_white_spaces(self.input_rows, recspec)
        self.rows = self._identify_records(
            self.input_rows, recspec, require_numbers = require_numbers,
            min_csim=min_csim
        )

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
            bool, re.split(RecordsExtractor.re_fields_separators, row)
        ))

    def _split_text_into_rows(self, text):
        '''Split text into rows. Remove empty rows.'''
        rows = re.split(RecordsExtractor.re_rows_separators, text)
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
                len(re.findall(RecordsExtractor.re_alphabetic_chars, field)), 
            row
        )), rows))

        for index, row in enumerate(fields_length_by_rows):
            field_with_max_chars = np.array(row).argmax()
            if field_with_max_chars > 0:
                rows[index][0:(field_with_max_chars+1)] = [
                    ' '.join(rows[index][0:(field_with_max_chars+1)])
                ]

        # 2. Get rid of leading numbers for labels
        for row in rows:
            # Verify whether the first item in the row is a label
            if not len(re.findall(RecordsExtractor.re_alphabetic_chars, row[0])):
                continue
            row[0] = re.sub(RecordsExtractor.re_leading_number, "", row[0])

        return rows

    def _identify_records(self, rows, recspec, min_csim=0.85, 
                          require_numbers=True, convert_numbers=True):
        stack = list()
        for index, row in enumerate(rows):
            # Check for presence of label and find the most similar label
            # in specification.
            label_tokens = find_ngrams(row[0], n=1, min_len=2, 
                                       remove_non_alphabetic=True)
            if label_tokens:
                csims = list(map(
                    lambda spec: (
                        spec["id"], 
                        cos_similarity(spec["ngrams"], label_tokens)
                    ), 
                    recspec
                ))

            # Check for presence of numbers in the row
            row_numbers_count = sum(map(util.is_number, row))

            if label_tokens:
                if row_numbers_count:
                    numbers = row[-row_numbers_count:]
                else:
                    numbers = None

                try:
                    s_label, s_numbers, s_csims, s_index = stack.pop()
                except IndexError:
                    stack.append((label_tokens, numbers, csims, (index,)))
                else:
                    if not (numbers and s_numbers):
                        ext_label = label_tokens + s_label
                        ext_csims = list(map(
                            lambda spec: (
                                spec["id"], 
                                cos_similarity(spec["ngrams"], ext_label)
                            ), 
                            recspec
                        ))

                        item_selector = operator.itemgetter(1)
                        max_ext_csims = max(ext_csims, key=item_selector)[1]
                        max_s_csims = max(s_csims, key=item_selector)[1]
                        max_csims = max(csims, key=item_selector)[1]

                        if (max_ext_csims > max_s_csims
                                and max_ext_csims > max_csims
                                # preceeding label has to be driving force 
                                and max_s_csims > max_csims): 
                            numbers = numbers or s_numbers
                            stack.append((ext_label, numbers, ext_csims, 
                                          s_index + (index,)))
                            continue

                    stack.append((s_label, s_numbers, s_csims, s_index))
                    stack.append((label_tokens, numbers, csims, (index,)))
                    
            elif row_numbers_count:
                numbers = row[-row_numbers_count:] 
                try:
                    s_label, s_numbers, s_csims, s_index = stack.pop()
                except IndexError:
                    # numbers without preceeding labels - ignore them
                    pass
                else:
                    if s_label and not s_numbers:
                        stack.append((s_label, numbers, s_csims, 
                                      s_index + (index,)))
                    else: # numbers without preceeding labels - ignore them
                        stack.append((s_label, s_numbers, s_csims, s_index))
            else:
                continue

        # Reduce stack
        ident_records = list()
        for label, numbers, csims, rows_indices in stack:
            if require_numbers and not numbers:
                continue
            max_csim = max(csims, key=operator.itemgetter(1))[1]
            if max_csim > min_csim:
                spec_id = sorted(
                    ((id, csim) for id, csim in csims 
                        #if (abs(csim - max_csim) < 1e-10 and csim > min_csim)),
                        if csim > min_csim),
                    key = operator.itemgetter(1)
                )
                if convert_numbers:
                    numbers = [ util.convert_to_number(num) for num in numbers ]
                ident_records.append(
                    (spec_id, numbers, rows_indices)
                )

        # Remove duplicates/Choose the row with the highest csims
        taken_keys = set()
        taken_rows = list()
        final_records = list()

        while True:
            data = list(
                (label.pop(), numbers, index, row_no) 
                for row_no, (label, numbers, index) in enumerate(ident_records)
                    if label and label[-1][0] not in taken_keys
                       and not any(set(index) & rows for rows in taken_rows)
            )  
            if not data:
                break

            for k, g in itertools.groupby(
                    sorted(data, key=lambda item: item[0][0], reverse=True), 
                    lambda item: item[0][0]
                ):
                selected_record = max(g, key=lambda item: item[0][1])
                final_records.append(selected_record[:-1])
                taken_keys.add(k)
                taken_rows.append(set(selected_record[2]))

        return sorted(final_records, key=lambda item: item[2][0], reverse=False)

    def _fix_white_spaces(self, rows, recspec):
        '''
        Fix broken labels. Sometimes the words are split with white spaces
        without any reason. Concatenate all words and then split long string
        into tokens.
        '''
        # Create vocabulary from specification
        voc = set(self.voc or tuple()) | set( 
            map(str, reduce(
                operator.add, 
                map(operator.itemgetter("ngrams"), recspec)
            ))
        )

        # Create list of bigrams
        zip_ngrams = map(
            lambda spec: zip(spec["ngrams"][:-1], spec["ngrams"][1:]), 
            recspec
        )
        bigrams = set()
        for item in zip_ngrams:
            bigrams.update(map(lambda ngram: ngram[0] + ngram[1], item))

        # Fix labels
        for row in rows:
            if not len(re.findall(RecordsExtractor.re_alphabetic_chars, row[0])):
                continue
            label_without_spaces = re.sub(' ', '', row[0])
            pot_labels = self._split_sentence_into_tokens(
                label_without_spaces, voc
            )
            if pot_labels: # label fixed, there are some results
                if len(pot_labels) == 1: # one potential label, no much choice
                    fixed_label = pot_labels[0]
                else: # more than one potentail label
                    # Choose the label with the largest number of identified 
                    # bigrams
                    temp_bigrams = [(index, set(find_ngrams(label, n=2))) 
                                     for index, label in enumerate(pot_labels)]
                    labels_bigrams = list(filter(lambda item: bool(item[1]), 
                                                 temp_bigrams))
                    if labels_bigrams:
                        labels_fit = sorted([
                            (index, len(bigram & bigrams) / len(bigram)) 
                             for index, bigram in labels_bigrams
                        ], key=operator.itemgetter(1), reverse=True)
                        fixed_label = pot_labels[labels_fit[0][0]]
                    else: # there are no bigrams, choose the longest unigram
                        fixed_label = max(pot_labels, key=len)

            else: # unabel to fix the label, return original label
                fixed_label = row[0]

            row[0] = fixed_label

        return rows

    def _split_sentence_into_tokens(self, sentence, voc):
        '''Split sentence in accordance with vocabulary.'''
        stack = [(list(), sentence)]
        results = list()

        re_voc = [re.compile("^" + word, flags=re.IGNORECASE) for word in voc]

        while stack:
            tokens, sentence = stack.pop()
            tokens_match = list(filter(
                bool, (re.match(re_word, sentence) for re_word in re_voc)
            ))
            if tokens_match:
                for match in tokens_match:
                    stack.append(
                        (tokens + [sentence[slice(*match.span())]], 
                         sentence[match.end():])
                    )
            else:
                sentence = sentence[1:]
                if not sentence:
                    if tokens:
                        results.append(' '.join(tokens))
                else:
                    stack.append((tokens, sentence))

        return results