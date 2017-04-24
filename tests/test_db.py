import unittest

from sqlalchemy import Column, Integer

from db import SQLAlchemy
from db.models import Base


# Clear all tables objects from metadata
Base.metadata.clear()

# Create a table for tests.
class TestModel(Base):
	'''Table for test'''
	__tablename__ = "test"

	id = Column(Integer, primary_key=True)
	number = Column(Integer)

	def __init__(self, number):
		self.number = number


class SQLAlchemyTest(unittest.TestCase):

	def test_create_db(self):
		db = SQLAlchemy("sqlite:///:memory:")
		self.assertIsNotNone(db.engine)

	def test_session_is_active_from_the_very_beginning(self):
		db = SQLAlchemy("sqlite:///:memory:")
		self.assertTrue(db.session.is_active)

	def test_for_creating_table_in_db(self):
		db = SQLAlchemy("sqlite:///:memory:")
		db.create_all()
		self.assertTrue(db.engine.has_table("test"))

	def test_for_creating_records_in_db(self):
		db = SQLAlchemy("sqlite:///:memory")
		db.create_all()
		test_record = TestModel(5)
		db.session.add(test_record)
		db.session.commit()
		self.assertIsNotNone(test_record.id)

	def test_for_quering_db(self):
		db = SQLAlchemy("sqlite:///:memory")
		db.create_all()
		db.session.add(TestModel(5))
		db.session.commit()
		test_record = db.session.query(TestModel).first()
		self.assertEqual(test_record.number, 5)