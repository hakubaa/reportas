import unittest
import unittest.mock as mock
from datetime import datetime

from rparser.utils import convert_to_number, pdfinfo, determine_timerange


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