import unittest


from parser.nlp import cos_similarity, NGram


class CosSimilarityTest(unittest.TestCase):

	def test_calc_similarity_with_oneself(self):
		field = ["test", "my", "vector"]
		self.assertAlmostEqual(cos_similarity(field, field), 1)

	def test_calc_similarity_between_different_tuples(self):
		t1 = ("one", "two")
		t2 = ("four", "five")
		self.assertAlmostEqual(cos_similarity(t1, t2), 0)


class NGramTest(unittest.TestCase):

	def test_for_marging_two_ngrams(self):
		n1 = NGram("one", "two")
		n2 = NGram("three")
		n = n1 + n2
		self.assertEqual(n, NGram("one", "two", "three"))

	def test_for_adding_tokens_to_ngram(self):
		n1 = NGram("one", "two")
		n1 += ("three", "four")
		self.assertEqual(len(n1), 4)
		self.assertEqual(n1, NGram("one", "two", "three", "four"))