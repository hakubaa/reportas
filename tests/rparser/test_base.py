import unittest
from unittest import mock
import io

from rparser.base import (
    PDFFileIO, Document, UnevenTable, RecordsCollector,
    FinancialStatement
)
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
        
        
class UnevenTableTest(unittest.TestCase):
    
    def test_create_table_with_rows(self):
        text_table = "Label1\t10\t20\nLabel2\t120\t150"
        
        table = UnevenTable(text_table)

        self.assertEqual(len(table), 2)
        self.assertEqual(table[0][0], "Label1")
        self.assertEqual(table[0][2], "20")
        self.assertEqual(table[1][1], "120")
        
    def test_each_row_can_have_different_number_of_cells(self):
        text_table = "Label1\t10\t20\nLabel2\t10\nLabel3\t\5\t6\t7"
        
        table = UnevenTable(text_table)
        
        self.assertEqual(len(table), 3)
        self.assertEqual(len(table[0]), 3)
        self.assertEqual(len(table[1]), 2)
        self.assertEqual(len(table[2]), 4)
        
    def test_empty_rows_are_not_ignored(self):
        text_table = "Label1\t10\t20\n\nLabel2\t5\t9"
        
        table = UnevenTable(text_table)
        
        self.assertEqual(len(table), 3)
        
    def test_indexing_returns_selected_row(self):
        text_table = '''Label1    10    15
        Label2   100   200
        '''
        table = UnevenTable(text_table)

        row = table[0]

        self.assertCountEqual(row, ["Label1", "10", "15"])

    def test_slicing_table_create_new_table(self):
        text_table = """Label1    10    15
        Label2   100   200"""
        table = UnevenTable(text_table)   

        new_table = table[1:]

        self.assertIsInstance(new_table, UnevenTable)
        self.assertEqual(len(new_table), 1)


class RecordsCollectorTest(unittest.TestCase):

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

        fs = RecordsCollector.__new__(RecordsCollector) # do not init
        words = fs.extract_words_from_spec(spec)

        self.assertCountEqual(
            words, ["net", "profit", "sales", "cost", "income", "tax", "loss"]
        )

    def test_extract_bigrams_from_spec(self):
        spec = [
            {"ngrams": [NGram("net"), NGram("profit")]},
            {"ngrams": [NGram("sales"), NGram("revenues"), NGram("cost")]}      
        ]

        fs = RecordsCollector.__new__(RecordsCollector) # do not init
        bigrams = fs.extract_bigrams_from_spec(spec)

        self.assertIn(NGram('sales', 'revenues'), bigrams)
        self.assertIn(NGram('revenues', 'cost'), bigrams)
        self.assertIn(NGram('net', 'profit'), bigrams)
        
    def test_find_potential_labels_for_broken_label(self):
        fs = RecordsCollector.__new__(RecordsCollector) # do not init
        
        voc = ["net", "profit", "revenues", "income"]
        labels = fs.find_potential_labels("vnetscprofitss", voc)
        
        self.assertEqual(len(labels), 1)
        self.assertEqual(labels[0], "net profit")
        
    def test_adjust_table_fixes_broken_labels(self):
        spec = self.get_records_spec()
        table = UnevenTable("""
        REVE NUE      100  200
        N ET PROF IT   10   20
        TA X            5    2
        """)

        rc = RecordsCollector.__new__(RecordsCollector)
        table = rc.adjust_table(table, spec)
        
        self.assertEqual(table[1][0], "REVENUE")
        self.assertEqual(table[2][0], "NET PROFIT")
        self.assertEqual(table[3][0], "TA X") # no word in specs  
        
    def test_adjust_table_removes_reference_notes(self):
        spec = self.get_records_spec()
        table = UnevenTable("""
              Label1   20   120
        I.    Label2   5    15
              Label3   10   150
        II.   Label4    1    2
        """)
        
        rc = RecordsCollector.__new__(RecordsCollector)
        table = rc.adjust_table(table, spec)

        self.assertEqual(table[1][0], "Label1")
        self.assertEqual(table[2][0], "Label2")
        self.assertEqual(table[3][0], "Label3")
        self.assertEqual(table[4][0], "Label4")
        
    def test_identify_records_declared_in_specification(self):
        spec = self.get_records_spec()
        table = UnevenTable("""
        REVENUE      100  200
        NET PROFIT    10   20
        TAX            5    2
        """)
    
        rc = RecordsCollector(table, spec)

        self.assertEqual(len(rc), 2) # two identified records
        self.assertIn("REVENUE", rc)
        self.assertIn("NET_PROFIT", rc)
        self.assertNotIn("TAX", rc)
        
    def test_records_data_are_stored_as_values_of_dict(self):
        spec = self.get_records_spec()
        table = UnevenTable("""
        REVENUE      100  200
        NET PROFIT    10   20
        TAX            5    2
        """)
    
        rc = RecordsCollector(table, spec)

        self.assertEqual(rc["REVENUE"], [100, 200])
        self.assertEqual(rc["NET_PROFIT"], [10, 20])
        
    def test_empty_values_represented_by_minus_are_interpreated_as_zeros(self):
        spec = self.get_records_spec()
        table = UnevenTable("""
        REVENUE      100    -
        NET PROFIT    -    20
        TAX            5    2
        """)
        
        rc = RecordsCollector(table, spec)
        
        self.assertEqual(rc["REVENUE"][1], 0)
        self.assertEqual(rc["NET_PROFIT"][0], 0)

    def test_records_map_contains_rows_no_for_every_record(self):
        spec = self.get_records_spec()
        table = UnevenTable("""
        REVENUE      100    -
        NET PROFIT    -    20
        TAX            5    2
        """)
        
        rc = RecordsCollector(table, spec) 

        self.assertEqual(rc.records_map["REVENUE"], (1,))
        self.assertEqual(rc.records_map["NET_PROFIT"], (2,))
        

class FinancialStatementTest(unittest.TestCase):

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

    def test_test(self):
        spec = self.get_records_spec()
        text_table = """
        REVENUE      100  200
        NET PROFIT    10   20
        TAX            5    2
        """

        fc = FinancialStatement(text_table, spec)

        import pdb; pdb.set_trace()