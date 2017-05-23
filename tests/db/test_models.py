import unittest
from datetime import datetime

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

	# def test_for_creating_record_with_create_method(self):
	# 	rtype = FinRecordType.create(self.db.session, name="FIXED_ASSETS")
	# 	company = Company.create(self.db.session, name="TEST")
	# 	report = FinReport.create(
	# 		self.db.session, timestamp=datetime(2015, 3, 31), timerange=3
	# 	)
	# 	self.db.session.commit()
	# 	record = FinRecord.create(
	# 		self.db.session, rtype=rtype, value=5,
	# 		timestamp = datetime(2015, 3, 31), timerange=3,
	# 		company=company, report=report
	# 	)
	# 	self.db.session.add(record)
	# 	self.db.session.commit()
	# 	self.assertEqual(self.db.session.query(FinRecord).count(), 1)
        
  #   def test_for_updating_record_with_create_method(self):
  # 		rtype = FinRecordType.create(self.db.session, name="FIXED_ASSETS")
		# company = Company.create(self.db.session, name="TEST")
		# report = FinReport.create(
		#     self.db.session, timestamp=datetime(2015, 3, 31), timerange=3
		# )
		# report_new = FinReport.create(
		#     self.db.session, timestamp=datetime(2016, 3, 31), timerange=3
		# )
		# self.db.session.commit()      
	 #    record = FinRecord.create(
	 #        self.db.session, rtype=rtype, value=5,
	 #        timestamp = datetime(2015, 3, 31), timerange=3,
	 #        company=company, report=report
  #       )
  #       self.db.session.add(record)
  #       self.db.session.commit()
        
  #       record_new = FinRecord.create(
	 #        self.db.session, rtype=rtype, value=10,
	 #        timestamp = datetime(2015, 3, 31), timerange=3,
	 #        company=company, report=report_new
  #       )
  #       self.db.session.add(record_new)
  #       self.db.session.commit()
        
  #       record = self.db.session.query(FinRecord).first()
  #       self.assertEqual(record.value, 10)
  #       self.assertEqual(record.report, report_new)
        
  #   def test_create_raises_error_when_updating_with_old_data(self):
  #       rtype = FinRecordType.create(self.db.session, name="FIXED_ASSETS")
		# company = Company.create(self.db.session, name="TEST")
		# report = FinReport.create(
		#     self.db.session, timestamp=datetime(2015, 3, 31), timerange=3
		# )
		# report_new = FinReport.create(
		#     self.db.session, timestamp=datetime(2016, 3, 31), timerange=3
		# )
		# self.db.session.commit()      
	 #    record = FinRecord.create(
	 #        self.db.session, rtype=rtype, value=5,
	 #        timestamp = datetime(2015, 3, 31), timerange=3,
	 #        company=company, report=report
  #       )
  #       self.db.session.add(record)
  #       self.db.session.commit()
        
  #       record_new = FinRecord.create(
	 #        self.db.session, rtype=rtype, value=10,
	 #        timestamp = datetime(2015, 3, 31), timerange=3,
	 #        company=company, report=report_new
  #       )
  #       self.db.session.add(record_new)
  #       with self.assertRaises(Exception):
  #           self.db.session.commit()  
            
  #   def test_for_overriding_with_old_data(self):
  #         rtype = FinRecordType.create(self.db.session, name="FIXED_ASSETS")
		# company = Company.create(self.db.session, name="TEST")
		# report = FinReport.create(
		#     self.db.session, timestamp=datetime(2015, 3, 31), timerange=3
		# )
		# report_old = FinReport.create(
		#     self.db.session, timestamp=datetime(2014, 3, 31), timerange=3
		# )
		# self.db.session.commit()      
	 #    record = FinRecord.create(
	 #        self.db.session, rtype=rtype, value=5,
	 #        timestamp = datetime(2014, 3, 31), timerange=3,
	 #        company=company, report=report
  #       )
  #       self.db.session.add(record)
  #       self.db.session.commit()
        
  #       record_new = FinRecord.create(
	 #        self.db.session, rtype=rtype, value=10,
	 #        timestamp = datetime(2014, 3, 31), timerange=3,
	 #        company=company, report=report_old,
	 #        override=True
  #       )
  #       self.db.session.add(record_new)
  #       self.db.session.commit()
        
  #       record = self.db.session.query(FinRecord).first()
  #       self.assertEqual(record.value, 10)
  #       self.assertEqual(record.report, report_old)
  #       self.assertEqual(record.report.timestamp, datetime(2014, 3, 31))			
			

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