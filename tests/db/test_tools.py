import itertools
from datetime import datetime
from collections import UserDict
import unittest
import operator

from tests.db import DbTestCase

import db.tools as tools
import db.models as models



class UploadingSpecTest(DbTestCase):

	def setUp(self):
		super().setUp()
		models.FinancialStatementType.insert_defaults(self.db.session)

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
		ftype = self.db.session.query(models.FinancialStatementType).\
		            filter_by(name="cfs").one()	
		spec = tools.get_records_reprs(self.db.session, ftype=ftype)
		self.assertEqual(len(spec), 1)
		self.assertEqual(spec[0]["name"], "CF#CFFO")


class CompaniesReprsTest(DbTestCase):

	def setUp(self):
		super().setUp()
		models.FinancialStatementType.insert_defaults(self.db.session)
		
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