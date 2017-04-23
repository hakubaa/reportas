import unittest

from util import convert_to_number


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