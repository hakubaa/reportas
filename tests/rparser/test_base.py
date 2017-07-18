import unittest
from unittest import mock
import io

from rparser.base import PDFFileIO, Document, FlawedTable, FinancialStatement
from rparser.nlp import NGram


@mock.patch("rparser.models.util.pdfinfo", return_value=({"Title": "Test"}, None))
@mock.patch("rparser.models.util.read_pdf",  
            return_value=(b"Page 1\n\x0cPage2\n\x0cPage3", None))
class PDFFileIOTest(unittest.TestCase):
    
    def test_for_calling_read_pdf_with_proper_path(self, mock_pdf, mock_info):
        doc = PDFFileIO("reports/test.pdf")
        self.assertIn("reports/test.pdf", mock_pdf.call_args[0])   
        
    def test_for_setting_info(self, mock_pdf, mock_info):
        doc = PDFFileIO("reports/test.pdf")
        self.assertTrue(hasattr(doc, "file_info"))
        self.assertEqual(doc.file_info["Title"], "Test")
        
    def test_read_a_line_from_the_file(self, mock_pdf, mock_info):
        doc = PDFFileIO("fake.pdf")
        first_line = doc.readline()
        self.assertEqual(first_line.rstrip(b"\n"), b"Page 1")
        
    def test_read_whole_content_of_the_file(self, mock_pdf, mock_info):
        doc = PDFFileIO("path_to_file.pdf")
        content = doc.read()
        self.assertEqual(content, mock_pdf.return_value[0])
        
    def test_wrap_PDFFileIO_with_TextIOWrapper(self, mock_pdf, mock_info):
        doc = io.TextIOWrapper(
            PDFFileIO("path_to_file.pdf"), encoding="UTF-8", newline="\n"
        )
        first_line = doc.readline()
        self.assertEqual(first_line.rstrip("\n"), "Page 1")
        
    def test_raises_OSError_when_pdf_reader_fails(self, mock_pdf, mock_inf):
        mock_pdf.return_value = (
            b'', b"I/O Error: Couldn't open file 'path_to_file.pdf: "
                 b"No such file or directory.\n"
        )
        with self.assertRaises(OSError):
            PDFFileIO("path_to_file.pdf")


class DocumentTest(unittest.TestCase):
    
    def get_stream(self):
        return io.StringIO(
            "Page 0 Row 0\nPage 0 Row 1\x0c"
            "Page 1 Row 0\nPage 1 Row 1\x0c"
            "Page 2 Row 0\nPage 2 Row 1"
        )
    
    def test_len_returns_number_of_pages(self):
        doc = Document(self.get_stream())
        self.assertEqual(len(doc), 3)

    def test_document_implements_iterator_protocol(self):
        doc = Document(self.get_stream())
        iter(doc)

    def test_for_accessing_particular_page(self):
        doc = Document(self.get_stream())
        page = doc[1]
        self.assertEqual(page, "Page 1 Row 0\nPage 1 Row 1")

    def test_slicing_of_document_creates_new_document(self):
        doc = Document(self.get_stream())
        new_doc = doc[1:3]
        self.assertIsInstance(new_doc, Document)
        self.assertEqual(len(new_doc), 2)
        self.assertEqual(new_doc[0], "Page 1 Row 0\nPage 1 Row 1")
        
    def test_indexing_raises_exception_when_page_is_out_of_range(self):
        doc = Document(self.get_stream())
        with self.assertRaises(IndexError):
            page_out_of_range = doc[9999]
            
    def test_documents_with_the_same_content_have_the_same_hash(self):
        doc1 = Document(io.StringIO("Content\x0cof\x0cdocument."))
        doc2 = Document(io.StringIO("Content\x0cof\x0cdocument."))
        self.assertEqual(hash(doc1), hash(doc2))

    def test_documents_with_the_same_content_are_equal(self):
        doc1 = Document(io.StringIO("Content\x0cof\x0cdocument."))
        doc2 = Document(io.StringIO("Content\x0cof\x0cdocument."))    
        self.assertEqual(doc1, doc2)
        
    def test_for_accessing_rows_of_document(self):
        doc = Document(self.get_stream())
        rows = doc.rows
        self.assertEqual(rows[0], (0, 0, 0, "Page 0 Row 0"))
        self.assertEqual(rows[1], (1, 0, 1, "Page 0 Row 1"))
        self.assertEqual(rows[2], (2, 1, 0, "Page 1 Row 0"))
        self.assertEqual(rows[3], (3, 1, 1, "Page 1 Row 1"))
        self.assertEqual(rows[4], (4, 2, 0, "Page 2 Row 0"))
        self.assertEqual(rows[5], (5, 2, 1, "Page 2 Row 1"))
        
        
class FlawedTableTest(unittest.TestCase):
    
    def test_create_table_with_rows(self):
        text_table = "Label1\t10\t20\nLabel2\t120\t150"
        
        table = FlawedTable(text_table, byrows=True)

        self.assertEqual(len(table), 2)
        self.assertEqual(table[0][0], "Label1")
        self.assertEqual(table[0][2], "20")
        self.assertEqual(table[1][1], "120")
        
    def test_each_row_can_have_different_number_of_cells(self):
        text_table = "Label1\t10\t20\nLabel2\t10\nLabel3\t\5\t6\t7"
        
        table = FlawedTable(text_table, byrows=True)
        
        self.assertEqual(len(table), 3)
        self.assertEqual(len(table[0]), 3)
        self.assertEqual(len(table[1]), 2)
        self.assertEqual(len(table[2]), 4)
        
    def test_empty_rows_are_ignored(self):
        text_table = "Label1\t10\t20\n\nLabel2\t5\t9"
        
        table = FlawedTable(text_table, byrows=True)
        
        self.assertEqual(len(table), 2)
        
    def test_create_table_by_columns(self):
        text_table = """
        Label1    10    15
        Label2   100   200
        """
        
        table = FlawedTable(text_table, byrows=False)
        
        self.assertEqual(len(table), 2)
        self.assertEqual(table[0][1], "10")
        self.assertEqual(table[1][2], "200")

    def test_indexing_returns_selected_row(self):
        text_table = """
        Label1    10    15
        Label2   100   200
        """
        table = FlawedTable(text_table, byrows=False)

        row = table[0]

        self.assertCountEqual(row, ["Label1", "10", "15"])

    def test_slicing_table_create_new_table(self):
        text_table = """
        Label1    10    15
        Label2   100   200
        """
        table = FlawedTable(text_table, byrows=False)   

        new_table = table[1:]

        self.assertIsInstance(new_table, FlawedTable)
        self.assertEqual(len(new_table), 1)
        
    def test_create_table_by_columns_copes_with_short_rows(self):
        text_table = """
        Label0    5
        Label1    10    15
        Label2   100   200
        """
        
        table = FlawedTable(text_table, byrows=False)
        
        self.assertEqual(len(table), 3)
        self.assertEqual(table[0][0], "Label0")
        self.assertEqual(table[0][2], "")
        self.assertEqual(table[2][2], "200")


    @unittest.skip
    def test_clean_labels_removes_reference_numbers_from_front(self):
        text_table = """
           Label1   20   120
        1) Label2   5    15
           Label3   10   150
        2) Label4    1    2
        """
        
        table = FlawedTable(text_table)
        table.clean_lables()
        
        self.assertEqual(table[0][0], "Label1")
        self.assertEqual(table[1][0], "Label2")
        self.assertEqual(table[2][0], "Label3")
        self.assertEqual(table[3][0], "Lable4")
    

class FinancialStatementTest(unittest.TestCase):

    def create_table_clean(self):
        text_table = """
        REVENUE      100  200
        NET PROFIT    10   20
        TAX            5    2
        """
        table = FlawedTable(text_table)
        return table

    def create_table_broken(self):
        text_table = """
        REVE NUE      100  200
        N ET PROF IT   10   20
        TA X            5    2
        """
        table = FlawedTable(text_table)
        return table

    def get_records_spec(self):
        spec = [
            {
                "name": "NET_PROFIT", 
                "ngrams": [NGram("net"), NGram("profit")] 
            },
            {
                "name": "REVENUE",
                "ngrams": [NGram("revenue")]
            },
            {
                "name": "REVENUE",
                "ngrams": [NGram("sales"), NGram("revenues")]
            }      
        ]
        return spec

    def test_extract_words_from_spec(self):
        spec = [
            {"ngrams": [NGram("net profit"), NGram("sales income tax")]},
            {"ngrams": [NGram("sales cost")]},
            {"ngrams": [NGram("loss")]}
        ]

        fs = FinancialStatement.__new__(FinancialStatement) # do not init
        words = fs.extract_words_from_spec(spec)

        self.assertCountEqual(
            words, ["net", "profit", "sales", "cost", "income", "tax", "loss"]
        )

    def test_extract_bigrams_from_spec(self):
        spec = [
            {"ngrams": [NGram("net"), NGram("profit")]},
            {"ngrams": [NGram("sales"), NGram("revenues"), NGram("cost")]}      
        ]

        fs = FinancialStatement.__new__(FinancialStatement) # do not init
        bigrams = fs.extract_bigrams_from_spec(spec)

        self.assertIn(NGram('sales', 'revenues'), bigrams)
        self.assertIn(NGram('revenues', 'cost'), bigrams)
        self.assertIn(NGram('net', 'profit'), bigrams)

    def test_clean_lables_fix_white_spaces(self):
        table = self.create_table_broken()
        spec = self.get_records_spec()

        fs = FinancialStatement(table, spec)

        self.assertEqual(table[0][0], "REVENUE")
        self.assertEqual(table[1][0], "NET PROFIT")
        self.assertEqual(table[2][0], "TA X") # no word in specs