import itertools

from tests.db import DbTestCase

from db.util import upload_finrecords_spec
from db.models import FinRecordType, FinRecordTypeRepr


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