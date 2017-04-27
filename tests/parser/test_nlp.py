import unittest


from parser.nlp import cos_similarity
from parser.models import Field


class CosSimilarityTest(unittest.TestCase):

	def test_calc_similarity_with_oneself(self):
		field = Field("Test my vector")
		self.assertAlmostEqual(cos_similarity(field, field), 1)

	def test_calc_similarity_between_different_tuples(self):
		t1 = ("one", "two")
		t2 = ("four", "five")
		self.assertAlmostEqual(cos_similarity(t1, t2), 0)

