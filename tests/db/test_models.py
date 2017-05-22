import unittest
from datetime import datetime

from db import SQLAlchemy
from db.models import FinReport, FinRecord, FinRecordType

from tests.db import DbTestCase


class FinRecordTypeTest(DbTestCase):

	def test_for_uniqueness_of_names(self):
		rtype = FinRecordType("TEST")
		self.db.session.add(rtype)
		self.db.session.commit()

		with self.assertRaises(Exception):
			rtype = FinRecordType("TEST")
			self.db.session.add(rtype)
			self.db.session.commit()
	

class FinRecordTest(DbTestCase):

	def test_relationship_with_recordtype(self):
		rtype = FinRecordType("FIXED_ASSETS")
		self.db.session.add(rtype)
		self.db.session.commit()

		record = FinRecord(rtype, 10, datetime(2015, 1, 1, 0, 0, 0), 3)
		self.db.session.add(record)
		self.db.session.commit()

		self.assertEqual(len(rtype.records), 1)
		self.assertEqual(rtype.records[0], record)

	def test_for_raising_error_when_overriding_specific_record(self):
		rtype = FinRecordType("FIXED_ASSETS")
		self.db.session.add(rtype)
		self.db.session.commit()

		record = FinRecord(rtype, 10, datetime(2015, 1, 1, 0, 0, 0), 3)
		self.db.session.add(record)
		self.db.session.commit()

		with self.assertRaises(Exception):
			record = FinRecord(rtype, 10, datetime(2015, 1, 1, 0, 0, 0), 3)
			self.db.session.add(record)
			self.db.session.commit()
			

class ReportTest(DbTestCase):

	def test_for_adding_record_to_report(self):
		report = FinReport(datetime(2015, 3, 31, 0, 0, 0), 3)
		self.db.session.add(report)
		self.db.session.commit()

		rtype = FinRecordType("FIXED_ASSETS")
		self.db.session.add(rtype)
		record = FinRecord(rtype, 10, datetime(2015, 1, 1, 0, 0, 0), 12)
		self.db.session.add(record)
		self.db.session.commit()

		report.add_record(record)
		self.db.session.commit()

		self.assertEqual(len(report.records), 1)
		self.assertEqual(report.records[0], record)