import io
from functools import reduce
import operator
import re
import numbers
from collections import Counter

import numpy as np

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


class FlawedTable:
    '''
    Two-dimensional table. Expects str object and products table. Each row
    can have different number of cells. The table can be created by rows or
    by columns.
    '''
    RE_FIELDS_SEPARATORS = re.compile(r"(?:\s)*(?:\||\s{2,}|\t|;)(?:\s)*")
    RE_ROWS_SEPARATORS = re.compile(r"\n")

    
    def __init__(self, text, byrows=True):
        if byrows:
            self.rows = self.create_table_by_rows(text)
        else:
            self.rows = self.create_table_by_columns(text)
        
    def create_table_by_rows(self, text):
        init_rows = (
            self.split_into_cells(row)
            for row in self.split_into_rows(text)
        ) 
        rows = [row for row in init_rows if len(row) > 0]
        return rows

    def create_table_by_columns(self, text):
        rows = self.split_into_rows(text)
        cols = util.split_into_columns(rows)
        return self.transform_into_rows(cols)
        
    def split_into_cells(self, row):
        cells = re.split(self.RE_FIELDS_SEPARATORS, row)
        return [ cell for cell in cells if cell ]
        
    def split_into_rows(self, text):
        rows = re.split(self.RE_ROWS_SEPARATORS, text)
        return [ row for row in rows if not row.isspace() ]

    def transform_into_rows(self, cols):
        rows = list(map(list, zip(*cols)))
        rows = [ [ cell.strip() for cell in row ] for row in rows ]
        rows = [ row for row in rows if any(map(bool, row)) ]
        return rows

    def __len__(self):
        if not self.rows:
            return 0
        return len(self.rows)
        
    def __iter__(self):
        return iter(self.rows)

    def __getitem__(self, index):
        cls = type(self)
        if isinstance(index, slice):
            instance = cls.__new__(cls)
            instance.rows = self.rows[index]
            return instance
        elif isinstance(index, numbers.Integral):
            return self.rows[index]
        else:
            msg = "{cls.__name__} indices must be integers"
            raise TypeError(msg.format(cls=cls))


class FinancialStatement:

    RE_ALPHABETIC_CHARS = re.compile(
        r"[a-zA-ZąćęłńóśźżĄĘŁŃÓŚŹŻ]"
    )
    RE_NOTE_REFERENCE = re.compile(
        r"^(?:Nota)?(?:\s)*(c(\d+)(?:\.\d+)*|(M{0,4}(CM|CD|D?C{0,3})"
        r"(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})))(\.|\)| )(?:\s)*"
    ) 

    def __init__(
        self, table, records_spec, voc=None, timerange=None, timestamp=None
    ):
        self.default_timerange = timerange
        self.default_timestamp = timestamp
        self.records_spec = records_spec
        self.voc = voc or list()
        self.table = table

        self.voc.extend(self.extract_words_from_spec(records_spec))
        self.clean_labels()

        self.records = util.identify_records(
            self.table, records_spec, require_numbers=True, min_csim=0.85
        )
        self.uom = util.identify_unit_of_measure(self.table)

    def extract_words_from_spec(self, spec):
        words = [
            str(ngram).split() for item in spec for ngram in item["ngrams"]
        ]
        unique_words = set(reduce(operator.add, words))
        return list(unique_words)

    def clean_labels(self):
        self.remove_note_references()
        bigrams = self.extract_bigrams_from_spec(self.records_spec)
        self.fix_white_spaces_in_labels(bigrams)

    def remove_note_references(self):
        '''
        In some rows the leading term is note reference. We want to have labels
        at first positions, so note references have to be removed.
        '''
        
        # 1. Count alphabetic chars in cells 
        cells_len = [ 
            [ self.count_alphabetic_chars(cell) for cell in row ] 
            for row in self.table
        ]
    
        # 2. Join the longest cell in terms of alpha chars with all 
        #    preceeding cells
        for index, row in enumerate(cells_len):
            cell_with_max_chars = np.array(row).argmax()
            if cell_with_max_chars > 0:
                self.table[index][0:(cell_with_max_chars+1)] = [
                    ' '.join(self.table[index][0:(cell_with_max_chars+1)])
                ]
    
        # 3. Remove leading note reference
        for row in self.table:
            # Verify whether the first item in the row is a label
            if not len(re.findall(self.RE_ALPHABETIC_CHARS, row[0])):
                continue
            row[0] = re.sub(self.RE_NOTE_REFERENCE, "", row[0])
    
        
    def count_alphabetic_chars(self, string):
        return len(re.findall(self.RE_ALPHABETIC_CHARS, string))

    def extract_bigrams_from_spec(self, spec):
        zip_ngrams = map(
            lambda spec: zip(spec["ngrams"][:-1], spec["ngrams"][1:]), spec
        )
        bigrams = set()
        for item in zip_ngrams:
            bigrams.update(map(lambda ngram: ngram[0] + ngram[1], item))
        return bigrams

    def fix_white_spaces_in_labels(self, bigrams=None):
        '''
        Fix broken labels. Sometimes the words are split with white spaces
        without any reason. Concatenate all words and then split long string
        into tokens.
        '''
        for index, row in enumerate(self.table):
            if self.count_alphabetic_chars(row[0]) == 0:
                continue
        
            label = re.sub(' ', '', row[0])
            pot_labels = self.find_potential_labels(label)
            
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

            self.table[index][0] = fixed_label

    def find_potential_labels(self, sentence):
        '''Split sentence in accordance with vocabulary.'''
        stack = [(list(), sentence)]
        results = list()
    
        re_voc = [
            re.compile("^" + word, flags=re.IGNORECASE) 
            for word in self.voc
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