# -*- coding: utf-8 -*

from functools import reduce
from collections import Counter, UserDict, OrderedDict
from datetime import datetime

import operator
import itertools
import reprlib
import numbers
import pickle
import re
from enum import Enum
import warnings
from copy import deepcopy

import nltk
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

from parser.nlp import NGram, find_ngrams, cos_similarity, STOP_WORDS
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
        self.info, errors = util.pdfinfo(docpath)

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

        # Decrease the probability for pages containing selected set of 
        # financial data.
        for index, ngrams_page in enumerate(ngrams_by_pages):
            if ((NGram("wybrane", "dane") in ngrams_page 
                and NGram("dane", "finansowe") in ngrams_page) or
                (NGram("wybrane", "skonsolidowane") in ngrams_page 
                and NGram("skonsolidowane", "dane") in ngrams_page
                and NGram("dane", "finansowe") in ngrams_page)
            ):
                # decrease the probabilty
                prob_by_pages[index] = prob_by_pages[index] * 0.5

        max_prob = max(prob_by_pages)
        page_with_max_prob = min(
            page for page, prob in enumerate(prob_by_pages) 
                 if abs(prob-max_prob) < 0.02
        )
        # page_with_max_prob = prob_by_pages.argmax()

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


class RecordsExtractor(UserDict):

    re_fields_separators = re.compile(r"(?:\s)*(?:\||\s{2,}|\t|;)(?:\s)*")
    re_rows_separators = re.compile(r"\n")
    re_alphabetic_chars = re.compile(r"[A-Za-zżźćńółęąśŻŹĆĄŚĘŁÓŃ]")
    re_leading_number = re.compile(
        r"^(?:Nota)?(?:\s)*(c(\d+)(?:\.\d+)*|(M{0,4}(CM|CD|D?C{0,3})"
        r"(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})))(\.|\)| )(?:\s)*"
    ) 
    def __init__(self, text, recspec, require_numbers=True, 
                 remove_non_ascii=True, min_csim=0.85, fix_white_spaces=True,
                 voc=None):
        self.voc = voc # used by _fix_white_spaces
        if remove_non_ascii:
            text = util.remove_non_ascii(text)
        self.text = text
        self.input_rows = self._extract_rows(text)
        temp_rows = [row[1] for row in deepcopy(self.input_rows)]
        temp_rows = self._preprocess_labels(temp_rows)
        if fix_white_spaces:
            temp_rows = self._fix_white_spaces(temp_rows, recspec)
        # temp_rows = self._remove_column_with_note_reference(temp_rows)
        records = self._identify_records(
            temp_rows, recspec, require_numbers = require_numbers,
            min_csim=min_csim
        )
        self.records = self._remove_column_with_note_reference(records)
        # Update input rows - add marker for rows with identified records
        vip_rows = reduce(
            operator.add, 
            itertools.chain(map(operator.itemgetter(-1), self.records))
        )
        for i, row in enumerate(self.input_rows):
            self.input_rows[i] = row + (int(i in vip_rows),)

        self.data = OrderedDict()
        for row in self.records:
            self.data[row[0][0]] = row[1]
        self.names = list()

    def update_names(self, timerange=None, timestamp=None):
        '''
        Update names. Takes into account additional information like 
        timerange and timestamp of the report.
        '''
        vip_rows = [index for index, _, flag in self.input_rows if flag == 1]
        min_vip_rows = max(min(vip_rows) - 10, 0)
        rows_with_labels = list(range(min_vip_rows, min(vip_rows)))
        text_rows = self._split_text_into_rows(self.text)

        text_labels = '\n'.join(
            row for index, row in text_rows if index in rows_with_labels if row
        )
        text_numbers = '\n'.join(
            row for index, row in text_rows if index in vip_rows if row
        )

        cols = util.split_text_into_columns(text_labels + "\n" + text_numbers)
        cols = [ 
            re.sub(" + ", " ", ' '.join(col[0:len(rows_with_labels)])) 
            for col in cols if col 
        ]

        # Find timeranges and timestamps by columns
        tranges = list(map(
            operator.itemgetter(-1), 
            [[None] + tr for tr in map(util.determine_timerange, cols)]
        ))[-self.ncols:]

        dates = list(map(
            lambda item: item[-1][0],
            [dt for dt in map(util.find_dates, cols) 
                if dt and dt[-1][0][2] in (28, 29, 30, 31)] # last day of the month
        ))[-self.ncols:]

        # Find timeranges and timestamps by rows if search by columns
        # have failed

        if not (all(map(bool, tranges)) and all(map(bool, dates)) 
                and all(map(lambda date: all(map(bool, date)), dates))
                and len(tranges) == self.ncols and len(dates) == self.ncols):
            rows = text_labels.split("\n")
            temp_tranges = (
                [ item for item in trange if item > 2] 
                for trange in filter(
                    bool, map(util.determine_timerange, reversed(rows))
                )
            )
            rows_tranges = next(temp_tranges, [])[-self.ncols:]
  
            rows_dates = list(map(
                operator.itemgetter(0), 
                next(filter(bool, map(util.find_dates, reversed(rows))), [])
            ))
            rows_dates = [ 
                date for date in rows_dates 
                if date[2] is None or date[2] in (28, 29, 30, 31) 
            ]

            if (all(map(bool, rows_tranges)) and all(map(bool, rows_dates))
                    and len(rows_dates) == len(rows_tranges) 
                    and len(rows_dates) == self.ncols):
                tranges = rows_tranges
                dates = rows_dates
            else:
                # timestamps in rows seem to be more reliable
                if (len(rows_dates) == self.ncols 
                    and all(map(bool, rows_dates))
                    and (
                        not all(map(bool, dates)) 
                        or len(dates) != self.ncols
                        or (
                            all(all(map(bool, date)) for date in rows_dates)
                            and not all(all(map(bool, date)) for date in dates)
                        )
                        or len(set(rows_dates)) > len(set(dates))
                    )
                ):
                    dates = rows_dates

                # information about timeragne is above the table
                if not all(map(bool, tranges)) and any(map(bool, rows_tranges)):
                    # tranges = (rows_tranges * len(dates))[0:len(dates)]
                    trange_for_dates = int(len(dates) / len(rows_tranges))
                    tranges = list(
                        itertools.chain.from_iterable(
                            itertools.repeat(x, trange_for_dates)
                            for x in rows_tranges * len(dates) # extend 
                            # rows_tranges by factor of len(dates), it is 
                            # required in situation when number of datas
                            # is odd and number of tranges is even
                        )
                    )[0:len(dates)]

        # check for two dates in every column
        coltrs = list()
        for trange, tms in zip(tranges, dates):
            if not trange:
                trange = timerange
            if not all(map(bool, tms)):
                year, month, day = tms
                if not year:
                    year = timestamp.year
                if not month and not day:
                    if timestamp:
                        month = timestamp.month
                        day = timestamp.day
                    else:
                        month = 12
                        day = 31
                if not day:
                    days_in_month = {
                        1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
                        7: 31, 8: 31, 9:30, 10: 31, 11: 30, 12:31
                    }
                    day = days_in_month[month]
                tms = (year, month, day)
            coltrs.append((trange, tms))

        if coltrs:
            self.names = coltrs

    def _split_row_into_fields(self, row):
        '''Split text into separate fields.'''
        return list(filter( # use filter to remove empty fields ('')
            bool, re.split(RecordsExtractor.re_fields_separators, row)
        ))

    def _split_text_into_rows(self, text):
        '''Split text into rows. Remove empty rows.'''
        rows = re.split(RecordsExtractor.re_rows_separators, text)
        rows = [ (i, row) for i, row in enumerate(rows) if not row.isspace() ]
        return rows

    def _extract_rows(self, text):
        '''Create simple table. Each row as separate list of fields.'''
        table = [ (row[0], self._split_row_into_fields(row[1]))
                 for row in self._split_text_into_rows(text)]
        table = [ row for row in table if row[1] ] # remove empty rows
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

                        max_csims = max(csims, key=item_selector)[1]
                        max_s_csims = max(s_csims, key=item_selector)[1]
                        max_ext_csims = max(ext_csims, key=item_selector)[1]
                        
                        if ((max_ext_csims > max_s_csims or 
                                abs(max_ext_csims - max_s_csims) < 1e-10)
                                and max_ext_csims > max_csims
                                # preceeding label has to be driving force 
                                and (
                                    max_s_csims > max_csims 
                                    or abs(max_s_csims - max_csims) < 1e-10
                                )): 
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
                    if s_label:
                        # probably the id of the note
                        if not s_numbers:
                            s_numbers = numbers
                        elif len(s_numbers) == 1:
                            s_numbers.extend(numbers)
                        else: # some lost numbers - ignore
                            pass 
                        stack.append((s_label, s_numbers, s_csims, 
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

        # Distirbution of rows
        rows_dist = reduce(
            operator.add, map(operator.itemgetter(-1), ident_records)
        )
        rows_dist_q50 = float(np.percentile(np.array(rows_dist), 50))

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
                group = list(g)
                max_sim = max(list(map(lambda x: x[0][1], group)))
                selected_record = sorted([ 
                    (abs(record[2][0] - rows_dist_q50),) + record 
                    for record in group if abs(record[0][1] - max_sim) < 1e-10 
                ], key=operator.itemgetter(0))[0][1:]
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

    def _remove_column_with_note_reference(self, records):
        '''Remove column with note reference.'''
        note_column = None # init value 
        
        # Select numbers from records
        rows = list(map(operator.itemgetter(1), records))

        # Select rows 
        max_freq = max(map(len, rows))
        mode_freq = Counter(map(len, rows)).most_common(1)[0][0]

        if max_freq < 3: # there are always at least two columns
            return records

        full_rows = [row for row in rows if len(row) == max_freq]
        mode_rows = [row for row in rows if len(row) == mode_freq]

        last_col_index = next(map(len, full_rows)) - 1

        # Is there any column with more None than numbers ?
        temp = [
            [ 1 if item is None else 0 for item in row ]
            for row in full_rows
        ]
        sum_of_nones = list(reduce(lambda x, y: map(operator.add, x, y), temp))
        max_sum = max(enumerate(sum_of_nones), key=operator.itemgetter(1))
        if max_sum[1] > len(temp)*0.5:
            # note column have to be one of the marginal columns
            if max_sum[0] == 0 or max_sum[0] == last_col_index:
                note_column = max_sum[0]

        # No, there is not. Try something different.
        if not note_column:  

            if len(full_rows) > 5:

                data = np.array([ 
                    row for row in full_rows 
                    if all(item is not None for item in row) 
                ])

                sv_cols = [ #single value columns
                    index for index, col in enumerate(data.T.tolist()) 
                    if len(set(col)) == 1 
                ]

                if sv_cols and (sv_cols[0] == 0 or sv_cols[0] == last_col_index):
                    note_column = sv_coll
                else: 
                    #make decision on the base of correlation
                    corr = np.corrcoef(data, rowvar=0)
                    corr_mean_first_col = np.mean(corr[1:,0])
                    corr_mean_last_col = np.mean(corr[:-1,-1])

                    # Decision Rule
                    if corr_mean_first_col < 0.25:
                        note_column = 0
                    elif corr_mean_last_col < 0.25:
                        note_column = last_col_index

            elif max_freq != mode_freq: # small number of full rows
                # concatenate full rows and mode rows
                data_left = np.array(
                    mode_rows + list(map(lambda x: x[0:mode_freq], full_rows))
                )
                data_right = np.array(
                    mode_rows + list(map(lambda x: x[-mode_freq:], full_rows))
                )

                corr_left = np.corrcoef(data_left, rowvar=0)[0,1]
                corr_right = np.corrcoef(data_right, rowvar=0)[0,1]

                if corr_left < corr_right:
                    note_column = 0
                else:
                    note_column = last_col_index


        if note_column is not None: # There is a column with note reference.
            ncols = max_freq - 1
            new_records = list()
            if note_column == 0:
                for item, nums, page in records:
                    new_records.append((item, nums[-ncols:], page))
            else:
                for item, nums, page in records:
                    new_records.append((item, nums[0:ncols], page))
            records = new_records

        return records

    @property
    def ncols(self):
        return max(map(len, self.values()))


class FinancialReport(Document):
    nls_pages = SelfSearchingPage("parser/cls/nls.pkl", "nls_pages")
    bls_pages = SelfSearchingPage("parser/cls/balance.pkl", "bls_pages")
    cfs_pages = SelfSearchingPage("parser/cls/cfs.pkl", "cfs_pages")

    def __init__(self, *args, consolidated=True, timestamp=None, 
                 timerange=None, spec = None, voc=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.consolidated = consolidated
        self.timestamp = timestamp or self._recognize_timestamp()
        self.timerange = timerange or self._recognize_timerange()
        self.spec = spec or dict()
        self.voc = voc

    @property 
    def cfs(self):
        if not hasattr(self, "_cfs"):
            self._cfs = self._extract_records(
                self.cfs_pages, self.spec["cfs"], self.voc
            )
        return self._cfs

    @property
    def nls(self):
        if not hasattr(self, "_nls"):
            self._nls = self._extract_records(
                self.nls_pages, self.spec["nls"], self.voc
            )
        return self._nls

    @property
    def bls(self):
        if not hasattr(self, "_bls"):
            self._bls = self._extract_records(
                self.bls_pages, self.spec["bls"], self.voc
            )
        return self._bls

    def _recognize_timerange(self):
        '''Recognize timerange of financial report.'''
        sa_tokens = util.remove_non_ascii("półroczny półroczne").split()
        qr_tokens = util.remove_non_ascii(
                        "kwartalny kwartał kwartały kwartalne").split()
        # semiannual if not quarterly
        sa2_tokens = util.remove_non_ascii("śródroczne").split()

        # Make decision on the base of the first three pages
        tokens = set(map(operator.itemgetter(0), find_ngrams(
            '\n'.join(self[0:3]), n=1, remove_non_alphabetic=True,
            min_len=min(map(len, itertools.chain(qr_tokens, sa_tokens))),
            return_tuples=True
        )))

        if set(sa_tokens) & tokens:
            return 6

        if set(qr_tokens) & tokens:
            return 3

        if set(sa2_tokens) & tokens:
            return 6

        return 12

    def _recognize_timestamp(self):
        '''Recognize timestamp of financial report.'''
        text = util.remove_non_ascii('\n'.join(self))
        timestamps = list()

        for timestamp, _, flag in util.find_dates(text, re_days=r"(28|29|30|31)"):
            if flag:    
                try:
                    timestamps.append(datetime(
                        year=timestamp[0], month=timestamp[1], day=timestamp[2]
                    ))
                except ValueError:
                    pass # ignore cray dates

        if not timestamps: # check for availability of timestamps
            return None

        # Remove timestamps from years different than the most frequent year
        # appearing in the report.
        re_year = re.compile(r"((?:19|20)\d{2})")

        years = list()
        match_years = re.findall(re_year, text)
        if match_years:
            for year in match_years:
                years.append(int(year))
        report_year = Counter(years).most_common(1)[0][0]

        timestamps = [ timestamp for timestamp in timestamps
                                 if timestamp.year == report_year ]
        
        if not timestamps: # check for availability of timestamps
            return None

        # Remove timestamps older than creation date
        creation_date = self.info.get("CreationDate", None) \
                            or self.info.get("ModDate", None)
        if creation_date: 
            creation_date = datetime( # get rid of hours, minutes and seconds
                creation_date.year, creation_date.month, creation_date.day
            )

            timestamps = [ timestamp for timestamp in timestamps
                                     if timestamp < creation_date ]

        if not timestamps: # check for availability of timestamps
            return None

        # Select the most common timestamp
        report_timestamp = Counter(timestamps).most_common(1)[0][0]
        return report_timestamp

    def _extract_records(self, pages, spec, voc):
        if len(pages) == 1:
            text = self[pages[0]]
        else:
            text = '\n'.join(operator.itemgetter(*pages)(self))
        records = RecordsExtractor(text, spec, voc=voc)
        try:
            records.update_names(self.timerange, self.timestamp)
        except Exception: # not vital feature, ignore and show warning
            warnings.warn(
                "Unabel to determine names of columns: '{!r}'".format(self)
            )
        return records