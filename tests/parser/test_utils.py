import unittest
import unittest.mock as mock
from datetime import datetime

from parser.util import convert_to_number, pdfinfo, determine_timerange


class DetermineTimerangeTest(unittest.TestCase):

	def test_determine_timerange_1(self):
		text = "01.01.2016 - 31.09.2016"
		output = determine_timerange(text)
		self.assertEqual(output[0], 9)

	def test_determine_timerange_2(self):
		text = "01.01 - 31.12.2016"
		output = determine_timerange(text)
		self.assertEqual(output[0], 12)		

	def test_determine_timerange_3(self):
		text = "01.01.2016 - 31.12"
		output = determine_timerange(text)
		self.assertEqual(output[0], 12)				

	def test_determine_timerange_4(self):
		text = "Od 01.01.2016 do 31.12.2017"
		output = determine_timerange(text)
		self.assertEqual(output[0], 24)			

	def test_determine_timerange_5(self):
		text = "Za okres 7 miesięcy zakończony 31 marca 2015"
		output = determine_timerange(text)
		self.assertEqual(output[0], 7)

	def test_determine_timerange_6(self):
		text = "I kwartał 2015"
		output = determine_timerange(text)
		self.assertEqual(output[0], 3)			

	def test_determine_timerange_7(self):
		text = "I półrocze 2015"
		output = determine_timerange(text)
		self.assertEqual(output[0], 6)	

	def test_determine_timerange_8(self):
		text = "Rok zakończony 31.12.2016"
		output = determine_timerange(text)
		self.assertEqual(output[0], 12)			


@mock.patch("parser.util.subprocess.Popen")
class PdfinfoTest(unittest.TestCase):

	def set_mock(self, mmock):
		output = (b'Title:          (Microsoft Word - Skonsolidowany raport kwartalny Grupy Kapita\\263owej JAGO za 1Q 2010 rok)\nAuthor:         Bart.Dr\nCreator:        PrimoPDF http://www.priSmoSpdDFGf.com/\nProducer:       PDrimDoDPDF\nCreationDate:   Mon May 17 18:45:02 2010 CEST\nModDate:        Mon May 17 18:45:02 2010 CEST\nTagged:         no\nUserProperties: no\nSuspects:       no\nForm:           none\nJavaScript:     no\nPages:          77\nEncrypted:      no\nPage size:      595.28 x 841.89 pts (A4)\nPage rot:       0\nFile size:      8337485 bytes\nOptimized:      no\nPDF version:    1.3\n',
 None)
		mmock.return_value.communicate.return_value = output

	def test_for_passing_file_path(self, mock_popen):
		mock_popen.return_value.communicate.return_value = (None, None)
		output = pdfinfo("fake.pdf")
		self.assertIn("fake.pdf", mock_popen.call_args[0][0])

	def test_for_returning_dict_with_info(self, mock_popen):
		mock_popen.return_value.communicate.return_value = (None, None)
		output, errors = pdfinfo("fake.pdf")
		self.assertIsInstance(output, dict)

	def test_for_parsing_info_from_pdfinfo(self, mock_popen):
		self.set_mock(mock_popen)
		output, errors = pdfinfo("fake.pdf")
		self.assertIn("Title", output)
		self.assertEqual(output["Tagged"], "no")

	def test_for_converting_creation_and_modyfication_dates(self, mock_popen):
		self.set_mock(mock_popen)
		output, errors = pdfinfo("fake.pdf")
		self.assertIsInstance(output["CreationDate"], datetime)
		self.assertIsInstance(output["ModDate"], datetime)


class Convert2numberTest(unittest.TestCase):

	def test_convert_simple_numbers(self):
		output = convert_to_number("345")
		self.assertEqual(output, 345)

	def test_convert_floating_number(self):
		output = convert_to_number("3.14", decimal_mark=".")
		self.assertEqual(output, 3.14)

	def test_for_accepting_number(self):
		output = convert_to_number(3.14)
		self.assertEqual(output, 3.14)

	def test_convert_negative_number(self):
		output = convert_to_number("-3.14", decimal_mark=".")
		self.assertEqual(output, -3.14)

	def test_convert_number_within_parenthesis(self):
		output = convert_to_number("(3.14)", decimal_mark=".")
		self.assertEqual(output, -3.14)

	def test_convert_number_with_white_spaces(self):
		output = convert_to_number("-3 140 150")
		self.assertEqual(output, -3140150)

	def test_conver_number_with_comma_as_decimal_mark(self):
		output = convert_to_number("-3,14")
		self.assertEqual(output, -3.14)

	def test_convert_number_with_commas_as_thousands_serpator(self):
		output = convert_to_number("-3,140,150.99", decimal_mark=".")
		self.assertEqual(output, -3140150.99)

	def test_convert_number_with_dot_as_thousands_separator(self):
		output = convert_to_number("(3.140.150,99)")
		self.assertEqual(output, -3140150.99)

	def test_convert_number_converts_empty_string_to_zero(self):
		output = convert_to_number("")
		self.assertEqual(output, 0)

	def test_convert_number_converts_dash_to_zero(self):
		output = convert_to_number("-")
		self.assertEqual(output, 0)