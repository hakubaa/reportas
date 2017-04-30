from collections import UserList
import functools
import operator

import unittest
import unittest.mock as mock

from parser.models import Document, SelfSearchingPage, NGram, ASCITable


@mock.patch("parser.models.util.pdftotext",  
            return_value=(b"Page 1\n\x0cPage2\n\x0cPage3", None))
class DocumentTest(unittest.TestCase):

    def test_for_calling_pdftotext_in_constructor(self, mock_pdf):
        doc = Document("reports/test.pdf")
        self.assertIn("reports/test.pdf", mock_pdf.call_args[0])

    def test_len_returns_number_of_pages(self, mock_pdf):
        doc = Document("reports/test.pdf")
        self.assertEqual(len(doc), 3)

    def test_document_implements_iterator_protocol(self, mock_pdf):
        doc = Document("reports/test.pdf")
        iter(doc)

    def test_for_accessing_particular_page(self, moc_pdf):
        doc = Document("reports/test.pdf")
        page = doc[1]
        self.assertEqual(page, "Page2\n")


class NGramTest(unittest.TestCase):

    def test_creating_ngram_with_separate_words(self):
        ng = NGram("one", "two", "test")
        self.assertEqual(repr(ng), "NGram('one', 'two', 'test')")

    def test_for_raising_error_when_creating_ngram_without_words(self):
        with self.assertRaises(TypeError):
            ng = NGram()

    def test_for_raising_error_when_no_str_argument(self):
        with self.assertRaises(TypeError):
            ng = NGram("one", 2, "test")

    def test_ngrams_with_similar_words_have_the_same_hash(self):
        ng1 = NGram("one", "two", "four")
        ng2 = NGram("one", "two", "four")
        self.assertEqual(hash(ng1), hash(ng2))

    def test_ngrams_with_the_same_words_are_equal(self):
        ng1 = NGram("one", "two", "four")
        ng2 = NGram("one", "two", "four")
        self.assertEqual(ng1, ng2)        

    def test_ngrams_with_the_same_words_but_with_different_order_are_not_equal(self):
        ng1 = NGram("one", "two", "four")
        ng2 = NGram("one", "four", "two")
        self.assertNotEqual(ng1, ng2)      

    def test_indexing_ngram_returns_new_ngram_when_more_than_one_token(self):
        ng1 = NGram("one", "two", "three", "four")
        ng2 = ng1[slice(None, None, 2)]
        self.assertIsInstance(ng2, NGram)  

    def test_for_handling_slice_object(self):
        ng1 = NGram("one", "two", "three", "four")
        ng2 = ng1[slice(None, None, 2)]
        self.assertEqual(ng2, NGram("one", "three"))


class ASCITableTest(unittest.TestCase):

    def test_split_row_into_fields_does_not_split_sentances(self):
        row_str = "Net profit  very high  very low"
        table = ASCITable(row_str)
        fields = table._split_row_into_fields(row_str)
        self.assertEqual(len(fields), 3)
        self.assertEqual(fields[1], "very high")

    def test_split_row_into_fields_respects_different_separators(self):
        row_str = "Net profit  very high | very low\tmedium   none;  huge   "
        table = ASCITable(row_str)
        fields = table._split_row_into_fields(row_str)
        self.assertEqual(len(fields), 6)
        self.assertCountEqual(
            fields, 
            ["Net profit", "very high", "very low", "medium", "none", "huge"]
        )

    def test_spit_text_into_rows_returns_list_of_rows(self):
        text = "Income  12 000 | 13 000\nCosts  10 000 | 15 000"
        table = ASCITable(text)
        rows = table._split_text_into_rows(text)
        self.assertEqual(len(rows), 2)

    def test_split_text_into_rows_removes_empty_rows(self):
        text = "Income  12 000 | 13 000\n    \n            \nCosts  10 000 | 15 000"
        table = ASCITable(text)
        rows = table._split_text_into_rows(text)
        self.assertEqual(len(rows), 2)

    def test_extract_rows_returns_list_of_lists(self):
        text = """
        Consolidated Financial Statement
        Income  12 000 | 13 000\n    \n            \nCosts  10 000 | 15 000
        """
        table = ASCITable(text)
        st = table._extract_rows(text)
        self.assertEqual(len(st), 3)
        self.assertEqual(len(st[0]), 1)
        self.assertEqual(len(st[1]), 3)
        self.assertEqual(len(st[2]), 3)

    def test_standardize_rows_keeps_only_rows_with_numbers(self):
        text = """
        Consolidated Financial Statement
        Income  12 000 | 13 000\n    \n            \nCosts  10 000 | 15 000
        """
        table = ASCITable(text)
        rows = table._standardize_rows(table._extract_rows(text))
        self.assertEqual(len(rows), 2)

    def test_standarize_rows_returns_lists_with_equaly_len_lists(self):
        text = """
        Consolidated Financial Statement
        Income  12 000 | 13 000\n    \n            \nCosts  10 000 | 15 000
        """
        table = ASCITable(text)
        rows = table._standardize_rows(table._extract_rows(text))
        self.assertEqual(len(set(map(len, rows))), 1)