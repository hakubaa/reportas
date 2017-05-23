import itertools
from datetime import datetime
from collections import UserDict
import unittest

from tests.db import DbTestCase

import db.util as util
import db.models as models

from db.util import upload_finrecords_spec
from db.models import FinRecordType, FinRecordTypeRepr, Company, FinRecord


# create fake class representing FinancialReport (parser.models)
FinancialReport = type("FinancialReport", (object,), dict())


class UploadingReport(DbTestCase):

	def setUp(self):
		super().setUp()
		self.create_fake_spec()

	def create_fake_spec(self):
		testspec = [ 
		    {
		        "statement": "bls", "name": "BLS#FIXEDASSETS",
		        "repr": [ { "lang": "EN", "value": "Fixed assets" } ]
		    },
		    {
		        "statement": "bls", "name": "BLS#INVENTORY",
		        "repr": [ { "lang": "EN", "value": "Inventory" } ]
		    }

		]
		upload_finrecords_spec(self.db, testspec)

	def create_fake_report(self, timestamp=None, timerange=None):
		report = FinancialReport()
		report.timestamp = timestamp or datetime(2015, 3, 31, 0, 0, 0)
		report.timerange = timerange or 3
		report.nls = UserDict()
		report.nls.names = []
		report.bls = UserDict({
			"BLS#FIXEDASSETS": [100, 150],
			"BLS#INVENTORY": [50, 75]
		})
		report.bls.names = [(3, (2015, 3, 31)), (3, (2014, 3, 31))]
		report.cfs = UserDict()
		report.cfs.names = []
		company = Company.get_or_create(self.db.session, name="test")
		self.db.session.commit()
		report.company = { "id": company.id }
		return report

	def test_for_creating_record_in_db(self):
		report = self.create_fake_report()
		util.upload_report(self.db.session, report)
		self.assertEqual(self.db.session.query(models.FinReport).count(), 1)

	def test_upload_report_returns_newly_created_finreport(self):
		report = self.create_fake_report()
		report_db = util.upload_report(self.db.session, report)	
		self.assertIsNotNone(report_db)
		self.assertIsInstance(report_db, models.FinReport)

	def test_for_creating_report_with_proper_timestamp_and_timerange(self):
		report = self.create_fake_report(
			timestamp=datetime(2016, 12, 31), timerange=12
		)
		report_db = util.upload_report(self.db.session, report)
		self.assertEqual(report_db.timestamp, report.timestamp)
		self.assertEqual(report_db.timerange, report.timerange)

	def test_for_uploading_records_from_bls(self):
		report = self.create_fake_report()
		report_db = util.upload_report(self.db.session, report)
		self.assertEqual(len(report_db.data), 4)

	def test_for_setting_proper_values_of_the_record(self):
		report = self.create_fake_report()
		report_db = util.upload_report(self.db.session, report)
		record = self.db.session.query(models.FinRecord).\
		                         filter_by(value=150).first()
		self.assertEqual(record.timestamp, datetime(2014, 3, 31))
		self.assertEqual(record.timerange, 3)
		self.assertEqual(record.report, report_db)
		rtype = self.db.session.query(models.FinRecordType).\
		                        filter_by(name="BLS#FIXEDASSETS").one()
		self.assertEqual(record.rtype, rtype)

	def test_for_updating_records_when_new_data(self):
		report = self.create_fake_report(
			timestamp=datetime(2015, 3, 31), timerange=3
		)
		util.upload_report(self.db.session, report)
		report = self.create_fake_report(
			timestamp=datetime(2016, 3, 31), timerange=3
		)
		report.bls = UserDict({
			"BLS#FIXEDASSETS": [300, 200],
			"BLS#INVENTORY": [150, 100]
		})
		report.bls.names = [(3, (2016, 3, 31)), (3, (2015, 3, 31))]
		util.upload_report(self.db.session, report)

		record = self.db.session.query(FinRecord).join(FinRecordType).\
			filter(FinRecordType.name == "BLS#FIXEDASSETS",
				   FinRecord.timestamp == datetime(2015, 3, 31)
			).one()
		self.assertEqual(record.value, 200)
		self.assertEqual(self.db.session.query(FinRecord).count(), 6)

	def test_for_raising_exception_when_upload_already_saved_report(self):
		report = self.create_fake_report()
		util.upload_report(self.db.session, report)
		with self.assertRaises(Exception):
			util.upload_report(self.db.session, report)

	def test_overriding_previous_report_deletes_also_the_records(self):
		report = self.create_fake_report(
			timestamp=datetime(2015, 3, 31), timerange=3
		)
		report.bls = UserDict({
			"BLS#FIXEDASSETS": [300, 200]
		})
		report.bls.names = [(3, (2015, 3, 31)), (3, (2014, 3, 31))]
		util.upload_report(self.db.session, report)	

		report = self.create_fake_report(
			timestamp=datetime(2015, 3, 31), timerange=3
		)
		report.bls = UserDict({
			"BLS#INVENTORY": [150, 100]
		})
		report.bls.names = [(3, (2015, 3, 31)), (3, (2014, 3, 31))]
		util.upload_report(self.db.session, report, override=True)

		self.assertEqual(self.db.session.query(FinRecord).count(), 2)	
		self.assertEqual(
			self.db.session.query(FinRecord).join(FinRecordType).\
				filter(FinRecordType.name == "BLS#INVENTORY").count(), 
			2
		)


class UploadingSpecTest(DbTestCase):

	def test_for_creating_records_types(self):
		testspec = [ 
			{ "statement": "cfs", "name": "CF#CFFO" }, 
		    { "statement": "cfs", "name": "CF#CFFI" }
		]
		upload_finrecords_spec(self.db, testspec)
		names = list(itertools.chain(
			*self.db.session.query(FinRecordType.name).all()
		))
		self.assertEqual(self.db.session.query(FinRecordType).count(), 2)
		self.assertCountEqual(names, [testspec[0]["name"], testspec[1]["name"]])

	def test_for_creating_records_types_with_repr(self):
		testspec = [ 
			{ 
				"statement": "cfs", "name": "CF#CFFO",
				"repr": [ 
					{ "lang": "PL", "value": "Przepływy operacyjne" },
					{ "lang": "EN", "value": "Cash flows" }
				]
			} 
		]
		upload_finrecords_spec(self.db, testspec)
		values = list(itertools.chain(
			*self.db.session.query(FinRecordTypeRepr.value).all()
		))
		self.assertEqual(self.db.session.query(FinRecordTypeRepr).count(), 2)
		self.assertCountEqual(
			values, 
			[testspec[0]["repr"][0]["value"], testspec[0]["repr"][1]["value"]]
		)

	def test_for_setting_proper_relation_between_type_and_repr(self):
		testspec = [ 
			{ 
				"statement": "cfs", "name": "CF#CFFO",
				"repr": [ 
					{ "lang": "PL", "value": "Przepływy operacyjne" }
				]
			} 
		]
		upload_finrecords_spec(self.db, testspec)
		finrecord_type = self.db.session.query(FinRecordType).first()
		type_repr = self.db.session.query(FinRecordTypeRepr).first()
		self.assertEqual(type_repr.rtype, finrecord_type)