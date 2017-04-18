from collections import UserList

import unittest
import unittest.mock as mock

from models import Document, SelfSearchingPage, NGram


@mock.patch("models.pdftotext",  
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


class SelfSearchingPageTest(unittest.TestCase):

    def test_for_calculating_simple_cover_rate(self):
        ssp = SelfSearchingPage("test", ["test", "one"])
        cover_rate, tokens = ssp._calc_simple_cover_rate(
            "One     test             will       concern     ..."
        ) 
        self.assertEqual(tokens, 5)
        self.assertEqual(cover_rate, 2/5)
        
    def test_simple_cover_rate_for_empty_text_returns_0_0(self):
        ssp = SelfSearchingPage("test", ["test", "one"])
        cr, tokens = ssp._calc_simple_cover_rate("")
        self.assertEqual((cr, tokens), (0, 0))

    def test___get__sets_attr_inside_instance(self):
        instance = UserList(["page one", "page two", "page test one"])
        ssp = SelfSearchingPage("test", ["test", "one"])
        ssp.__get__(instance, None)
        self.assertTrue(hasattr(instance, "test"))

    def test___get__returns_the_most_covered_pages(self):
        document = UserList(["page one", "page two", "page test one"])
        ssp = SelfSearchingPage("test", ["test", "page"])
        pages = ssp.__get__(document, None)
        self.assertEqual(len(pages), 1)
        self.assertEqual(pages[0], document[2])


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