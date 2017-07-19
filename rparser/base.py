import io
import re
import numbers
import operator
import itertools
from copy import deepcopy
from functools import reduce
from collections import Counter, UserDict, OrderedDict

import numpy as np

from rparser import nlp
from rparser import util


class PDFFileIO(io.BytesIO):
    '''
    PDFFileIO represents PDF file as an in-memory bytes buffer. It inherits
    io.BytesIO and provides similar interface.
    '''
    def __init__(self, path, first_page=None, last_page=None, **kwargs):
        pdf_content, errors = util.read_pdf(
            path, layout=True, first_page=first_page, last_page=last_page
        ) 
        if errors:
            raise OSError(errors.decode(encoding="utf-8", errors="ignore"))
            
        super().__init__(pdf_content)
        self.path = path
        
    @property
    def file_info(self):
        if not hasattr(self, "_info"):
            self._info, errors = util.pdfinfo(self.path)
        return self._info


class Document:
    '''
    Represents a text as a collection of pages. Expects text stream or 
    file-like object and produces str objects.
    '''
    def __init__(self, stream, newpage="\x0c", newline="\n"):
        self.pages = stream.read().split(newpage)
        self.newline = newline
        self.newpage = newpage
        self.info = getattr(stream, "file_info", None) 

    def __len__(self):
        return len(self.pages)

    def __iter__(self):
        return iter(self.pages)
        
    def __hash__(self):
        return hash(reduce(operator.xor, map(hash, self)))

    def __eq__(self, other):
        if len(self) != len(other): # different number of pages
            return False
        for self_page, other_page in zip(self, other):
            if self_page != other_page:
                return False
        return True

    def __getitem__(self, index):
        cls = type(self)
        if isinstance(index, slice):
            instance = cls(
                io.StringIO(self.newpage.join(self.pages[index])), 
                newpage=self.newpage, newline=self.newline
            )
            instance.info = self.info
            return instance
        elif isinstance(index, numbers.Integral):
            return self.pages[index]
        else:
            msg = "{cls.__name__} indices must be integers"
            raise TypeError(msg.format(cls=cls))

    @property
    def rows(self):
        '''
        Split document into rows. Returns list of tuples containing 
        document-level row number, page number, page-level row number and 
        content of a row.
        '''
        rows_aggregator = list()
        for page_no, page_text in enumerate(self):
            last_row_no = len(rows_aggregator)
            rows_aggregator.extend(
                (row_no + last_row_no, page_no, row_no, row_text)
                for row_no, row_text in enumerate(page_text.split(self.newline))
            )
        return rows_aggregator


class UnevenTable():
    '''Two-dimensional table. Expects str object and products table.'''
    
    RE_ROWS_SEPARATORS = re.compile(r"\n")
    RE_FIELDS_SEPARATORS = re.compile(r"(?:\s)*(?:\||\s{2,}|\t|;)(?:\s)*")

    def __init__(self, text):
        self.data = self.create_table(text)
        
    def create_table(self, text):
        rows = [
            self.split_into_cells(row)
            for row in self.split_into_rows(text)
        ]
        return rows
        
    def split_into_rows(self, text):
        rows = re.split(self.RE_ROWS_SEPARATORS, text)
        #rows = [ (i, row) for i, row in enumerate(rows) if not row.isspace() ]
        return rows

    def split_into_cells(self, row):
        cells = re.split(self.RE_FIELDS_SEPARATORS, row)
        return [ cell for cell in cells if cell ]

    def __len__(self):
        if not self.data:
            return 0
        return len(self.data)
        
    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, index):
        cls = type(self)
        if isinstance(index, slice):
            instance = cls.__new__(cls)
            instance.data = self.data[index]
            return instance
        elif isinstance(index, numbers.Integral):
            return self.data[index]
        else:
            msg = "{cls.__name__} indices must be integers"
            raise TypeError(msg.format(cls=cls))
        

class RecordsCollector(UserDict):
    ''' 
    Search for financial records in a text. Provides mapping protocol where 
    the keys are the names of identified records and the values are 
    corresponding financial data.
    '''
    
    RE_ALPHABETIC_CHARS = re.compile(
        r"[a-zA-ZąćęłńóśźżĄĘŁŃÓŚŹŻ]"
    )
    RE_NOTE_REFERENCE = re.compile(
        r"^(?:Nota)?(?:\s)*(c(\d+)(?:\.\d+)*|(M{0,4}(CM|CD|D?C{0,3})"
        r"(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})))(\.|\)| )(?:\s)*"
    )
    record_spec_id = "name" 
    
    def __init__(self, table, spec, voc=None):
        self.table = self.adjust_table(table, spec, voc)
        self.records = self.identify_records(self.table, spec)
        self.records_map = self.map_to_rows(self.records)
        # self.records_source = self.map_to_source(self.records, self.table)
        self.data = self.transform_to_dict(self.records)
        
    def adjust_table(self, table, spec, voc=None):
        voc = list(voc or list())
        voc.extend(self.extract_words_from_spec(spec))
        bigrams = self.extract_bigrams_from_spec(spec)
        
        table = self.remove_note_references(deepcopy(table))
        table = self.fix_white_spaces_in_labels(table, voc, bigrams)
        return table
        
    def extract_words_from_spec(self, spec):
        words = [
            str(ngram).split() for item in spec for ngram in item["ngrams"]
        ]
        unique_words = set(reduce(operator.add, words))
        return list(unique_words)
           
    def extract_bigrams_from_spec(self, spec):
        zip_ngrams = map(
            lambda spec: zip(spec["ngrams"][:-1], spec["ngrams"][1:]), spec
        )
        bigrams = set()
        for item in zip_ngrams:
            bigrams.update(map(lambda ngram: ngram[0] + ngram[1], item))
        return bigrams 
        
    def remove_note_references(self, table):
        '''
        In some rows the leading term is note reference. We want to have labels
        at first positions, so note references have to be removed.
        '''
        
        # 1. Count alphabetic chars in cells 
        cells_len = [ 
            [ self.count_alphabetic_chars(cell) for cell in row ] 
            for row in table
        ]

        # 2. Join the longest cell in terms of alpha chars with all 
        #    preceeding cells
        for index, row in enumerate(cells_len):
            if len(row) == 0: continue
            cell_with_max_chars = np.array(row).argmax()
            if cell_with_max_chars > 0:
                table[index][0:(cell_with_max_chars+1)] = [
                    ' '.join(table[index][0:(cell_with_max_chars+1)])
                ]
    
        # 3. Remove leading note reference
        for row in filter(len, table):
            # Verify whether the first item in the row is a label
            if not len(re.findall(self.RE_ALPHABETIC_CHARS, row[0])):
                continue
            row[0] = re.sub(self.RE_NOTE_REFERENCE, "", row[0])

        return table   
    
    def count_alphabetic_chars(self, string):
        return len(re.findall(self.RE_ALPHABETIC_CHARS, string))

    def fix_white_spaces_in_labels(self, table, voc, bigrams=None):
        '''
        Fix broken labels. Sometimes the words are split with white spaces
        without any reason. Concatenate all words and then split long string
        into tokens.
        '''
        for row in filter(len, table):
            if self.count_alphabetic_chars(row[0]) == 0:
                continue
        
            label = re.sub(' ', '', row[0])
            pot_labels = self.find_potential_labels(label, voc)
            
            if len(pot_labels) == 0:
                fixed_label = row[0] # label cannot be fixed
            elif len(pot_labels) == 1:
                fixed_label = pot_labels[0]
            else: 
                if not bigrams:
                    fixed_label = max(pot_labels, key=len)
                else:
                    # Choose the label with the largest number of 
                    # identified bigrams
                    labels_bigrams = [
                        (index, set(find_ngrams(label, n=2))) 
                        for index, label in enumerate(pot_labels)
                    ]
                    labels_bigrams = [ 
                        bigrams
                        for index, bigrams in labels_bigrams if len(bigrams) > 0    
                    ]
                    
                    if len(labels_bigrams) == 0:
                        # there are no bigrams, choose the longest unigram
                        fixed_label = max(pot_labels, key=len)   
                    else:
                        # Choose the label with the highest percent of 
                        # identified bigrams.
                        labels_fit = sorted([
                            (index, len(bigram & bigrams) / len(bigram)) 
                             for index, bigram in labels_bigrams
                        ], key=operator.itemgetter(1), reverse=True)
                        fixed_label = pot_labels[labels_fit[0][0]]

            row[0] = fixed_label

        return table

    def find_potential_labels(self, sentence, voc):
        '''Split sentence in accordance with vocabulary.'''
        stack = [(list(), sentence)]
        results = list()
    
        re_voc = [
            re.compile("^" + word, flags=re.IGNORECASE) 
            for word in voc
        ]
    
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

    def identify_records(
        self, table, recspec, min_csim=0.85, require_numbers=True, 
        convert_numbers=True
    ):
        stack = list()
        for index, row in enumerate(table):
            if len(row) == 0: continue

            # Check for presence of label and find the most similar label
            # in specification.
            label_tokens = nlp.find_ngrams(
                row[0], n=1, min_len=2, remove_non_alphabetic=True
            )
            if label_tokens:
                csims = list(map(
                    lambda spec: (
                        spec[self.record_spec_id], 
                        nlp.cos_similarity(spec["ngrams"], label_tokens)
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
                                spec[self.record_spec_id], 
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

    def map_to_rows(self, records):
        data = OrderedDict()
        for (rid, rsim), values, rows in records:
            data[rid] = rows
        return data

    # def map_to_source(self, records, table):
    #     data = OrderedDict()
    #     for (rid, rsim), values, rows in records:
    #         data[rid] = '\n'.join(table[row_no] for row_no in rows)
    #     return data

    def transform_to_dict(self, records):
        data = OrderedDict()
        for (rid, rsim), values, rows in records:
            data[rid] = values
        return data

    @property
    def ncols(self):
        return max(map(len, self.values()))


class FinancialStatement:
        
    def __init__(self, text, spec, timerange=None, timestamp=None, voc=None):
        self.table = UnevenTable(text)
        self.data = RecordsCollector(self.table, spec, voc)
        self.names = self.identify_names(
            self.data.records, text, timerange, timestamp
        )
        self.uom = self.identify_unit_of_measure(text)
        self.records_map = self.data.records_map
        
    def identify_names(self, records, text, timerange=None, timestamp=None):
        '''
        Update names. Takes into account additional information like 
        timerange and timestamp of the report.
        '''
        rows_with_records = reduce(
            operator.add, 
            itertools.chain(map(operator.itemgetter(-1), records))
        )

        min_vip_rows = max(min(rows_with_records) - 10, 0)
        rows_with_labels = list(range(min_vip_rows, min(rows_with_records)))
        text_rows = util.split_text_into_rows(text)

        text_labels = '\n'.join(
            row for index, row in text_rows if index in rows_with_labels if row
        )

        if not text_labels: # no text above records, no way to find names
            return list()

        text_numbers = '\n'.join(
            row for index, row in text_rows if index in rows_with_records if row
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
        ))[-records.ncols:]


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
            ))[-records.ncols:]

        # Find timeranges and timestamps by rows if search by columns
        # have failed

        if not (all(map(bool, tranges)) and all(map(bool, dates)) 
                and all(map(lambda date: all(map(bool, date)), dates))
                and len(tranges) == records.ncols and len(dates) == records.ncols):
            rows = text_labels.split("\n")
            temp_tranges = (
                [ item for item in trange if item > 2] 
                for trange in filter(
                    bool, map(util.determine_timerange, reversed(rows))
                )
            )
            rows_tranges = next(temp_tranges, [])[-records.ncols:]
      
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
                    and len(rows_dates) == records.ncols):
                tranges = rows_tranges
                dates = rows_dates
            else:
                # timestamps in rows seem to be more reliable
                if (len(rows_dates) == records.ncols 
                    and all(map(bool, rows_dates))
                    and (
                        not all(map(bool, dates)) 
                        or len(dates) != records.ncols
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

        return coltrs

    def identify_unit_of_measure(self, text):
        '''
        Identify unit of measure used to measure financial items. Return
        integer representing unit of measure (e.g. 1000 for thousands).
        '''
        re_thousands = re.compile(
            r"\btys(?:\.| |i[aą]?cach) ?(?:PLN|z[lł]?otych|z[lł]?)\b",
            flags = re.IGNORECASE
        )
        th_matches = re.findall(re_thousands, text)
        
        re_thousands000 = re.compile(r"\bPLN ?'?000\b", flags = re.IGNORECASE)
        th_matches.extend(re.findall(re_thousands000, text))
        
        re_millions = re.compile(
            r"\b(?:mln|milionach) ?(?:PLN|z[lł]?otych|z[lł]?)\b",
            flags = re.IGNORECASE
        )
        mln_matches = re.findall(re_millions, text)
        
        if th_matches and mln_matches: # return the most often unit
            if len(mln_matches) > len(th_matches):
                return 1000000
            else:
                return 1000
        
        if th_matches:
            return 1000
        
        if mln_matches:
            return 1000000
        
        return 1


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
        
    
class FinancialReport(Document):
    # Composition of Financial Statmenets
    # - bls - balance sheet
    # - cfs - cash flow statement
    # - ics - income statement
    
    ics_pages = SelfSearchingPage("parser/cls/ics.pkl", "ics_pages")
    bls_pages = SelfSearchingPage("parser/cls/balance.pkl", "bls_pages")
    cfs_pages = SelfSearchingPage("parser/cls/cfs.pkl", "cfs_pages")

    def __init__(self, *args, consolidated=True, timestamp=None, 
                 timerange=None, spec = None, voc=None, cspec=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.consolidated = consolidated
        self.timestamp = timestamp or self.recognize_timestamp()
        self.timerange = timerange or self.recognize_timerange()
        self.spec = spec or dict()
        self.voc = voc
        self.company = self.recognize_company(cspec)

    def get_bls_spec(self):
        return self.spec.get("bls", None)
    
    def get_ics_spec(self):
        return self.spec.get("ics", None)
    
    def eget_cfs_spec(self):
        return self.spec.get("cfs", None)
    
    @property
    def records(self):
        recs = dict()
        for stm in (self.bls, self.ics, self.cfs):
            try:
                recs.update(stm)
            except AttributeError:
                pass
        return recs  

    @property
    def records_map(self):
        rmap = dict()
        for stm in (self.bls, self.ics, self.cfs):
            try:
                rmap.update(stm.records_map)
            except AttributeError:
                pass
        return rmap

    @property
    def rows_map(self):
        rmap = dict()
        for stm in (self.bls, self.ics, self.cfs):
            try:
                rmap.update(stm.rows_map)
            except AttributeError:
                pass
        return rmap

    @property
    def records_source(self):
        isource = dict()
        for stm in (self.bls, self.ics, self.cfs):
            try:
                isource.update(stm.records_source)
            except AttributeError:
                pass
        return isource         

    @property 
    def cfs(self):
        if not hasattr(self, "_cfs"):
            self._cfs = self.extract_records(
                self.cfs_pages, self.get_cfs_spec(), self.voc
            )
        return self._cfs

    @property
    def ics(self):
        if not hasattr(self, "_ics"):
            self._ics = self.extract_records(
                self.ics_pages, sefl.get_ics_spec(), self.voc
            )
        return self._ics

    @property
    def bls(self):
        if not hasattr(self, "_bls"):
            self._bls = self.extract_records(
                self.bls_pages, self.get_bls_spec(), self.voc
            )
        return self._bls

    def recognize_timerange(self):
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

    def recognize_company(self, cspec, max_page=3, field="repr"):
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

    def recognize_timestamp(self):
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

    def extract_records(self, pages, spec, voc):
        if not spec: # empty spec, nothing can be done
            warnings.warn("No specification.")
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

        records = RecordsCollector(
            self.table_cls(text), spec, voc=voc, 
            first_row_number=preceeding_rows_count
        )

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

    def as_dict(self):
        '''Convert report to dictionary.'''
        data = dict()
        data["company"] = self.company
        data["timerange"] = self.timerange
        data["timestamp"] = self.timestamp

        data_ics = dict()
        data_ics["pages"] = self.ics_pages
        if self.ics:
            data_ics["units_of_measure"] = self.ics.uom
            data_ics["columns"] = [
                {"timerange": timerange, "timestamp": datetime(year, month, day)}
                for timerange, (year, month, day) in self.ics.names
            ]
            data_ics["records"] = list()
            for key, value in self.ics.items():
                record = {"name": key, "values": value, 
                          "rows": self.ics.records_map[key]}
                data_ics["records"].append(record)
        data["ics"] = data_ics

        data_bls = dict()
        data_bls["pages"] = self.bls_pages
        if self.bls:
            data_bls["units_of_measure"] = self.bls.uom
            data_bls["columns"] = [
                {"timerange": timerange, "timestamp": datetime(year, month, day)}
                for timerange, (year, month, day) in self.bls.names
            ]
            data_bls["records"] = list()
            for key, value in self.bls.items():
                record = {"name": key, "values": value, 
                          "rows": self.bls.records_map[key]}
                data_bls["records"].append(record)
        data["bls"] = data_bls

        data_cfs = dict()
        data_cfs["pages"] = self.cfs_pages
        if self.cfs:
            data_cfs["units_of_measure"] = self.cfs.uom
            data_cfs["columns"] = [
                {"timerange": timerange, "timestamp": datetime(year, month, day)}
                for timerange, (year, month, day) in self.cfs.names
            ]
            data_cfs["records"] = list()
            for key, value in self.cfs.items():
                record = {"name": key, "values": value, 
                          "rows": self.cfs.records_map[key]}
                data_cfs["records"].append(record)
        data["cfs"] = data_cfs

        return data