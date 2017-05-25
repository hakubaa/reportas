import unittest
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from db.models import FinReport, FinRecord, FinRecordType, Company
from tests.db import DbTestCase


class FinRecordTypeTest(DbTestCase):

	def test_for_uniqueness_of_names(self):
		rtype = FinRecordType(name="TEST")
		self.db.session.add(rtype)

		with self.assertRaises(IntegrityError):
			rtype = FinRecordType(name="TEST")
			self.db.session.add(rtype)
			self.db.session.commit()
	

class FinRecordTest(DbTestCase):

	def test_relationship_with_recordtype(self):
		rtype = FinRecordType.create(self.db.session, name="FIXED_ASSETS")
		company = Company.create(self.db.session, name="TEST")
		report = FinReport.create(
		    self.db.session, timestamp=datetime(2015, 3, 31), timerange=3,
		    company=company
		)

		record = FinRecord(rtype=rtype, value=10, 
			               timestamp=datetime(2015, 1, 1, 0, 0, 0), 
			               timerange=3,
			               company=company, report=report)
		self.db.session.add(record)
		self.db.session.commit()

		self.assertEqual(len(rtype.records), 1)
		self.assertEqual(rtype.records[0], record)

	def test_for_raising_error_when_overriding_specific_record(self):
		rtype = FinRecordType.create(self.db.session, name="FIXED_ASSETS")
		company = Company.create(self.db.session, name="TEST")
		company2 = Company.create(self.db.session, name="TEST2")
		report = FinReport.create(
		    self.db.session, timestamp=datetime(2015, 3, 31), timerange=3,
		    company=company
		)

		record = FinRecord(rtype=rtype, value=10, 
			               timestamp=datetime(2015, 1, 1, 0, 0, 0), 
			               timerange=3,
			               company=company, report=report)
		self.db.session.add(record)
		self.db.session.commit()

		with self.assertRaises(IntegrityError):
			record = FinRecord(rtype=rtype, value=10, 
				               timestamp=datetime(2015, 1, 1, 0, 0, 0), 
				               timeragne=3,
				               company=company, report=report)
			self.db.session.add(record)
			self.db.session.commit()

	def test_for_creating_record_with_create_method(self):
		rtype = FinRecordType.create(self.db.session, name="FIXED_ASSETS")
		company = Company.create(self.db.session, name="TEST")
		report = FinReport.create(
			self.db.session, timestamp=datetime(2015, 3, 31), timerange=3,
			company=company
		)
		self.db.session.commit()
		record = FinRecord.create(
			self.db.session, rtype=rtype, value=5,
			timestamp = datetime(2015, 3, 31), timerange=3,
			company=company, report=report
		)
		self.db.session.add(record)
		self.db.session.commit()
		self.assertEqual(self.db.session.query(FinRecord).count(), 1)
        
	def test_for_updating_record_with_create_or_update_method(self):
		rtype = FinRecordType.create(self.db.session, name="FIXED_ASSETS")
		company = Company.create(self.db.session, name="TEST")
		report = FinReport.create(
			self.db.session, timestamp=datetime(2015, 3, 31), timerange=3,
			company=company
		)
		report_new = FinReport.create(
			self.db.session, timestamp=datetime(2016, 3, 31), timerange=3,
			company=company
		)
		record = FinRecord.create(
			self.db.session, rtype=rtype, value=5,
			timestamp = datetime(2015, 3, 31), timerange=3,
			company=company, report=report
		)
		record_new = FinRecord.create_or_update(
			self.db.session, rtype=rtype, value=10,
			timestamp = datetime(2015, 3, 31), timerange=3,
			company=company, report=report_new
		)

		record = self.db.session.query(FinRecord).first()
		self.assertEqual(record.value, 10)
		self.assertEqual(record.report, report_new)
        
	def test_create_or_update_does_not_update_with_old_report(self):
		rtype = FinRecordType.create(self.db.session, name="FIXED_ASSETS")
		company = Company.create(self.db.session, name="TEST")
		report = FinReport.create(
			self.db.session, timestamp=datetime(2015, 3, 31), timerange=3,
			company=company
		)
		report_new = FinReport.create(
			self.db.session, timestamp=datetime(2014, 3, 31), timerange=3,
			company=company
		)
		record = FinRecord.create_or_update(
			self.db.session, rtype=rtype, value=5,
			timestamp = datetime(2014, 3, 31), timerange=3,
			company=company, report=report
		)
		FinRecord.create_or_update(
			self.db.session, rtype=rtype, value=10,
			timestamp = datetime(2014, 3, 31), timerange=3,
			company=company, report=report_new,
			override=False
		)
		self.db.session.commit()  

		record = self.db.session.query(FinRecord).first()
		self.assertEqual(record.value, 5)
		self.assertEqual(record.report, report)

	def test_for_overriding_with_old_data(self):
		rtype = FinRecordType.create(self.db.session, name="FIXED_ASSETS")
		company = Company.create(self.db.session, name="TEST")
		report = FinReport.create(
			self.db.session, timestamp=datetime(2015, 3, 31), timerange=3,
			company=company
		)
		report_old = FinReport.create(
			self.db.session, timestamp=datetime(2014, 3, 31), timerange=3,
			company=company
		)
		record = FinRecord.create_or_update(
			self.db.session, rtype=rtype, value=5,
			timestamp = datetime(2014, 3, 31), timerange=3,
			company=company, report=report
		)
		record_new = FinRecord.create_or_update(
			self.db.session, rtype=rtype, value=10,
			timestamp = datetime(2014, 3, 31), timerange=3,
			company=company, report=report_old,
			override=True
		)
		self.db.session.commit()

		record = self.db.session.query(FinRecord).first()
		self.assertEqual(record.value, 10)
		self.assertEqual(record.report, report_old)
		self.assertEqual(record.report.timestamp, datetime(2014, 3, 31))			
			

class ReportTest(DbTestCase):

	def test_for_adding_record_to_report(self):
		company = Company.create(self.db.session, name="TEST")
		report = FinReport.create(
			self.db.session, timestamp=datetime(2015, 3, 31), timerange=3,
			company=company
		)
		rtype = FinRecordType(name="FIXED_ASSETS")
		self.db.session.add(rtype)
		record = report.add_record(
			rtype=rtype, value=10, 
			timestamp=datetime(2015, 1, 1, 0, 0, 0), 
			timerange=12,
			company=company, report=report
		)
		self.db.session.commit()

		self.assertEqual(len(report.data), 1)
		self.assertEqual(report.data[0], record)

	def test_for_creating_report_with_create_method(self):
		company = Company.create(self.db.session, name="TEST")
		FinReport.create(
			self.db.session, timestamp=datetime(2015, 3, 31), timerange=3,
			company=company
		)
		self.db.session.commit()
		report = self.db.session.query(FinReport).first()
		self.assertEqual(report.timestamp, datetime(2015, 3, 31))
		self.assertEqual(report.timerange, 3)

	def test_get_or_create_creates_new_obj_if_not_exists(self):
		company = Company.create(self.db.session, name="TEST")
		record = FinReport.get_or_create(
			self.db.session, timestamp=datetime(2015, 3, 31), timerange=3,
			company=company
		)
		self.db.session.commit()
		report2 = self.db.session.query(FinReport).first()
		self.assertEqual(self.db.session.query(FinReport).count(), 1)
		self.assertEqual(record.id, report2.id)

	def test_get_or_create_gets_record_from_db(self):
		company = Company.create(self.db.session, name="TEST")
		record = FinReport(timestamp=datetime(2015, 3, 31), timerange=3,
			               company=company)
		self.db.session.add(record)
		self.db.session.commit()
		record2 = FinReport.get_or_create(
			self.db.session, timestamp=datetime(2015, 3, 31), timerange=3,
			company=company
		)
		self.assertEqual(record.id, record2.id)