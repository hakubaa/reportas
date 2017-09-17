import itertools
from datetime import datetime, date
from collections import UserDict
import unittest
import operator

from tests.db import DbTestCase
from tests.db.utils import *

import db.tools as tools
import db.utils as utils
import db.models as models



class UploadingSpecTest(DbTestCase):

	def setUp(self):
		super().setUp()
		models.FinancialStatement.insert_defaults(self.db.session)

	def test_for_creating_records_types(self):
		testspec = [ 
			{ "statement": "cfs", "name": "CF#CFFO" }, 
		    { "statement": "cfs", "name": "CF#CFFI" }
		]
		tools.upload_records_spec(self.db.session, testspec)
		names = list(itertools.chain(
			*self.db.session.query(models.RecordType.name).all()
		))
		self.assertEqual(self.db.session.query(models.RecordType).count(), 2)
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
		tools.upload_records_spec(self.db.session, testspec)
		values = list(itertools.chain(
			*self.db.session.query(models.RecordTypeRepr.value).all()
		))
		self.assertEqual(self.db.session.query(models.RecordTypeRepr).count(), 2)
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
		tools.upload_records_spec(self.db.session, testspec)
		finrecord_type = self.db.session.query(models.RecordType).first()
		type_repr = self.db.session.query(models.RecordTypeRepr).first()
		self.assertEqual(type_repr.rtype, finrecord_type)

	def test_get_records_reprs_returns_specification(self):
		testspec = [ 
			{ 
				"statement": "cfs", "name": "CF#CFFO",
				"repr": [ 
					{ "lang": "PL", "value": "Przepływy operacyjne" }
				]
			} 
		]
		tools.upload_records_spec(self.db.session, testspec)
		ftype = self.db.session.query(models.FinancialStatement).\
		            filter_by(name="cfs").one()	
		spec = tools.get_records_reprs(self.db.session, ftype=ftype)
		self.assertEqual(len(spec), 1)
		self.assertEqual(spec[0]["name"], "CF#CFFO")


class CompaniesReprsTest(DbTestCase):

	def setUp(self):
		super().setUp()
		models.FinancialStatement.insert_defaults(self.db.session)
		
	def test_get_companies_reprs_returns_isins_and_fullnames(self):
		company = models.Company.get_or_create(
			self.db.session, name="test", isin="test#isin", fullname="test"
		)
		self.db.session.commit()
		cspec = tools.get_companies_reprs(self.db.session)
		self.assertEqual(len(cspec), 1)
		self.assertEqual(cspec[0]["isin"], "test#isin")

	def test_get_companies_reprs_returns_companies_reprs(self):
		company = models.Company.get_or_create(
			self.db.session, name="test", isin="test#isin", fullname="test"
		)
		company.reprs.append(models.CompanyRepr(value="testowo"))
		self.db.session.commit()
		cspec = tools.get_companies_reprs(self.db.session)
		self.assertEqual(len(cspec), 2)
		self.assertEqual(len(set(map(operator.itemgetter("isin"), cspec))), 1)
		reprs = list(map(operator.itemgetter("repr"), cspec))
		self.assertCountEqual(reprs, ["test", "testowo"])

	def test_create_vocabulary_uses_records_reprs(self):
		testspec = [ 
			{ 
				"statement": "cfs", "name": "CF#CFFO",
				"repr": [ 
					{ "lang": "PL", "value": "Przepływy operacyjne" }
				]
			} 
		]
		tools.upload_records_spec(self.db.session, testspec)	
		voc = tools.create_vocabulary(self.db.session, remove_non_ascii=False)
		self.assertIn("operacyjne", voc)
		self.assertIn("przepływy", voc)

	def test_create_vocabulary_adds_extra_words(self):
		voc = tools.create_vocabulary(
			self.db.session, remove_non_ascii=True,
			extra_words = ("test", "create", "vocabulary")
		)
		self.assertIn("test", voc)
		self.assertIn("create", voc)
		self.assertIn("vocabulary", voc)


class MissingRecordsTest(DbTestCase):

    def test_create_missing_records(self):
        with self.db.session.no_autoflush:
            company = create_company(self.db.session, name="Test", isin="#TEST")
            ta, ca, fa = create_rtypes(self.db.session)
            self.db.session.add_all(create_records(self.db.session, [
                (company, ta, 0, date(2015, 12, 31), 100),
                (company, fa, 0, date(2017, 12, 31), 50)
            ]))
            schema = FinancialStatementLayout()
            schema.append_rtype(fa, 0)
            schema.append_rtype(ca, 1)
            schema.append_rtype(ta, 2)
            self.db.session.add(schema)
            self.db.session.commit()

            records = schema.get_records(company=company, timerange=0)
            records.extend(tools.create_missing_records(records, company, 12))

            self.assertEqual(len(records), 6)

            records = utils.group_objects(records, key=lambda x: x.rtype_id)
            records = sorted(records[ta.id], key=lambda x: x.timestamp)

            self.assertEqual(records[0].timestamp, date(2015, 12, 31))
            self.assertEqual(records[1].timestamp, date(2016, 12, 31))
            self.assertEqual(records[2].timestamp, date(2017, 12, 31))

    def test_end_of_month_test01(self):
        ref_date = date(2015, 3, 15)
    
        eom_date = utils.end_of_month(ref_date)        
        
        self.assertEqual(eom_date, date(2015, 3, 31))

    def test_end_of_month_plus_new_months(self):
        ref_date = date(2015, 3, 15)

        eom_date = utils.end_of_month(ref_date, 5)

        self.assertEqual(eom_date, date(2015, 8, 31))

    def test_datesrange_test01(self):
        start_date = date(2015, 3, 31)
        end_date = date(2015, 12, 31)

        dates = list(utils.datesrange(start_date, end_date, 3))

        self.assertEqual(len(dates), 4)
        self.assertCountEqual(dates, [date(2015, 3, 31), date(2015, 6, 30), 
            date(2015, 9, 30), date(2015, 12, 31)])

    def test_daterange_test02(self):
        start_date = date(2014, 9, 30)
        end_date = date(2015, 3, 31)

        dates = list(utils.datesrange(start_date, end_date, 3))

        self.assertEqual(len(dates), 3)
        self.assertCountEqual(dates, [date(2014, 9, 30), date(2014, 12, 31), 
            date(2015, 3, 31)])