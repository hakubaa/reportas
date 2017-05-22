import unittest

from db import SQLAlchemy

from db.models import FinRecord


class DbTestCase(unittest.TestCase):

	def setUp(self):
		self.db = SQLAlchemy("sqlite:///:memory:")
		self.db.create_all()

	def tearDown(self):
		self.db.drop_all()
