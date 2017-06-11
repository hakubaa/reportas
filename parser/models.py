# -*- coding: utf-8 -*

from functools import reduce
from collections import Counter, UserDict, OrderedDict, Iterable
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

    @property
    def rows(self):
        collector = list()
        global_row_no = 0
        for page_no, text in enumerate(self):
            for row_no, content in enumerate(text.split("\n")):
                collector.append((global_row_no, page_no, row_no, content))
                global_row_no += 1
        return collector


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

    def __init__(self, text, recspec, require_numbers=True, 
                 remove_nonascii=True, min_csim=0.85, fix_white_spaces=True,
                 voc=None, first_row_number=0):
        self.voc = voc # used by _fix_white_spaces
        self.input_text = text # save orignal text

        if remove_nonascii:
            text = util.remove_non_ascii(text)
        self.text = text
        self.input_rows = util.extract_rows(text)

        temp_rows = [row[1] for row in deepcopy(self.input_rows)]
        temp_rows = util.preprocess_labels(temp_rows)
        if fix_white_spaces:
            temp_rows = util.fix_white_spaces(temp_rows, voc, recspec)
        records = util.identify_records(
            temp_rows, recspec, require_numbers = require_numbers,
            min_csim=min_csim
        )
        self.records = self._remove_column_with_note_reference(records)

        self.items_map = dict() 
        for rid, nums, pages in self.records:
            self.items_map.update(
                itertools.zip_longest(
                    map(lambda x: self.input_rows[x][0] + first_row_number, 
                        pages), 
                    (rid[0],), fillvalue=rid[0])
            )

        self.items_source = dict()
        for (rid, rsim), nums, pages in self.records:
            content = operator.itemgetter(
                *list(map(lambda x: self.input_rows[x][0], pages))
            )(self.input_text.split("\n"))
            if not isinstance(content, str):
                content = "\n".join(content)
            self.items_source[rid] = content

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
        rows_with_records = reduce(
            operator.add, 
            itertools.chain(map(operator.itemgetter(-1), self.records))
        )
        vip_rows = [ 
            row[0] for i, row in enumerate(self.input_rows) 
            if i in rows_with_records 
        ]

        min_vip_rows = max(min(vip_rows) - 10, 0)
        rows_with_labels = list(range(min_vip_rows, min(vip_rows)))
        text_rows = util.split_text_into_rows(self.text)

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


        full_dates = [ 
            list(filter(lambda x: x[-1], dt))
            for dt in map(util.find_dates, cols) 
        ]
        dates = list(map(
            lambda item: item[-1][0],
            [dt for dt in full_dates if dt and dt[-1][0][2] in (28, 29, 30, 31)] 
        ))

        if not dates:
            dates = list(map(
                lambda item: item[-1][0],
                [dt for dt in map(util.find_dates, cols) 
                    if dt and dt[-1][0][2] in (28, 29, 30, 31)] 
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
                 timerange=None, spec = None, voc=None, cspec=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.consolidated = consolidated
        self.timestamp = timestamp or self._recognize_timestamp()
        self.timerange = timerange or self._recognize_timerange()
        self.spec = spec or dict()
        self.voc = voc
        self.company = self._recognize_company(cspec)

    @property
    def items_map(self):
        rmap = dict()
        for stm in (self.bls, self.nls, self.cfs):
            try:
                rmap.update(stm.items_map)
            except AttributeError:
                pass
        return rmap

    @property
    def items_source(self):
        isource = dict()
        for stm in (self.nls, self.nls, self.cfs):
            try:
                isource.update(stm.items_source)
            except AttributeError:
                pass
        return isource         

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
        sa_tokens = util.remove_non_ascii("pĂłĹ‚roczny pĂłĹ‚roczne").split()
        qr_tokens = util.remove_non_ascii(
                        "kwartalny kwartaĹ‚ kwartaĹ‚y kwartalne").split()
        # semiannual if not quarterly
        sa2_tokens = util.remove_non_ascii("Ĺ›rĂłdroczne").split()

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

    def _recognize_company(self, cspec, max_page=3, field="repr"):
        '''
        Recognize company of the report. The search is driven by full names
        and names of the companies. Choose the company which full name 
        appears the most frequently in the report.
        '''
        if not cspec: # not spec => not able to recognize company
            return None
            
        text = '\n'.join(self[0:max_page])
        text = re.sub(r"\bS\.?A(?:\.|\b)", "SA", text, flags=re.IGNORECASE)

        # 1. Make decision on the base of repr.

        cres = list() # list of tuples
        for comp in cspec:
            cfield = re.sub(r"\bS\.?A(?:\.|\b)", "SA", comp[field], 
                            flags=re.IGNORECASE).rstrip().lstrip()
            cres.append((
                comp["isin"],
                len(re.findall(cfield, text, flags=re.IGNORECASE)),
            ))
        cres = sorted(cres, key=lambda x: x[1], reverse=True)

        if cres[0][1] > 0: # any match
            isin = cres[0][0]
        else: # 2. Otherwise try modified version of TF-IDF
            text = '\n'.join(self)
            text = re.sub(r"\bS\.?A(?:\.|\b)", "SA", text, flags=re.IGNORECASE)
            text_voc = Counter(find_ngrams(text, n=1, min_len=2))
            names_ngrams = [
                (company["isin"], 
                 find_ngrams(company["repr"], n=1, min_len=2))
                for company in cspec
            ]
            names_voc = Counter(
                reduce(operator.add, map(operator.itemgetter(1), names_ngrams))
            )

            mtf = [
                (name[0], sum(text_voc[ng]/(names_voc[ng]**2) for ng in name[1]))
                for name in names_ngrams
            ]
            isin = max(mtf, key=lambda x: x[1])[0]

        return next(filter(lambda cp: cp["isin"] == isin, cspec)) 

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
        if not spec: # empty spec, nothing can be done
            return None

        if not isinstance(pages, Iterable):
            pages = (pages, )

        if len(pages) == 1:
            text = self[pages[0]]
        else:
            text = '\n'.join(operator.itemgetter(*pages)(self))

        preceeding_rows_count = 0
        for page in self[:min(pages)]:
            preceeding_rows_count += len(page.split("\n"))

        records = RecordsExtractor(
            text, spec, voc=voc, first_row_number=preceeding_rows_count
        )
        try:
            records.update_names(self.timerange, self.timestamp)
        except Exception: # not vital feature, ignore and show warning
            warnings.warn(
                "Unabel to determine names of columns: '{!r}'".format(self)
            )

        return records