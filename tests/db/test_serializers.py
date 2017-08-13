import unittest
import unittest.mock as mock
from datetime import datetime, date

from tests.db import DbTestCase
from db.serializers import *  
import db.models as models
from db.core import Model

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from marshmallow import fields
from marshmallow_sqlalchemy import field_for, ModelSchema


#-------------------------------------------------------------------------------

def create_ftype(session, name="bls"):
    ftype = models.FinancialStatementType(name=name)
    session.add(ftype)
    session.commit()
    return ftype

#-------------------------------------------------------------------------------

class CompanyReprSchemaTest(DbTestCase):

    def test_company_id_attribute_is_required(self):
        data = {"value": "Test Value"}
        obj, errors = CompanyReprSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("company_id", errors)

    def test_company_has_to_exist_in_db(self):
        data = {"value": "Test Value", "company_id": 1}
        obj, errors = CompanyReprSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("company_id", errors)

    def test_load_creates_new_companyrepr(self):
        company = models.Company(name="TEST", isin="#TEST")
        self.db.session.add(company)
        self.db.session.commit()
        data = {"value": "Test Value", "company_id": company.id}
        obj, errors = CompanyReprSchema().load(data, session=self.db.session)
        self.db.session.add(obj)
        self.db.session.commit()
        crepr = self.db.session.query(models.CompanyRepr).first()
        self.assertIsNotNone(crepr)
        self.assertEqual(crepr.value, data["value"])
        self.assertEqual(crepr.company, company)


class SectorSchemaTest(DbTestCase):

    def test_name_is_required(self):
        data = {"value": "That's not the name."}
        obj, errors = SectorSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("name", errors)

    def test_name_is_unique(self):
        sector = models.Sector(name="Media")
        self.db.session.add(sector)
        self.db.session.commit()

        data = {"name": "Media"}
        obj, errors = SectorSchema().load(data, session=self.db.session)

        self.assertTrue(errors)
        self.assertIn("name", errors)


class CompanySchemaTest(DbTestCase):

    def test_name_attribute_is_required(self):
        data = {"isin": "#test"}
        obj, errors = CompanySchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("name", errors)

    def test_isin_attribute_is_required(self):
        data = {"name": "test"}
        obj, errors = CompanySchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("isin", errors)

    def test_isin_has_to_be_unique(self):
        self.db.session.add(models.Company(name="TEST", isin="#TEST"))
        data = {"isin": "#TEST", "name": "Company"}
        obj, errors = CompanySchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("isin", errors)

    def test_sector_has_to_exist_in_db(self):
        data = {"isin": "#TEST", "name": "BLA", "sector_id": 1}

        obj, errors = CompanySchema().load(data, session=self.db.session)

        self.assertTrue(errors)
        self.assertIn("sector_id", errors)

    def test_load_creates_new_company(self):
        data = {"name": "Test Name", "isin": "#ISIN"}
        obj, errors = CompanySchema().load(data, session=self.db.session)
        self.db.session.add(obj)
        self.db.session.commit()
        company = self.db.session.query(models.Company).first()
        self.assertIsNotNone(company)
        self.assertEqual(company.name, data["name"])
        self.assertEqual(company.isin, data["isin"])

    def test_deserialized_data_contains_company_reprs(self):
        company = models.Company(name="TEST", isin="#TEST")
        self.db.session.add(company)
        self.db.session.flush()
        self.db.session.add_all((
            models.CompanyRepr(value="Repr #1", company_id=company.id),
            models.CompanyRepr(value="Repr #2", company_id=company.id),
            models.CompanyRepr(value="Repr #3", company_id=company.id)
        ))
        self.db.session.commit()
        data = CompanySchema().dump(company).data
        self.assertEqual(len(data["reprs"]), 3)
        values = [ item["value"] for item in data["reprs"] ]
        self.assertCountEqual(values, ["Repr #1", "Repr #2", "Repr #3"])

    def test_deserialized_data_contains_sector_name(self):
        sector = models.Sector(name="Media")
        company = models.Company(name="TEST", isin="#TEST", sector=sector)
        self.db.session.add_all((sector, company))
        self.db.session.commit()

        data = CompanySchema().dump(company).data

        self.assertIn("sector", data)
        self.assertEqual(data["sector"]["name"], "Media")

    def test_create_new_company_with_reprs(self):
        '''
        The test requires to fix fields.py file in marshmallow package.
        Inherti session form parent object.
        '''
        data = {
            "reprs": [{"value": "TEST TEST"}, {"value": "TESTOWO"}], 
            "isin": "TEST", "name": "TEST"
        } 
        obj, errors = CompanySchema().load(data, session=self.db.session)
        self.db.session.add(obj)
        self.db.session.commit()

        self.assertTrue(self.db.session.query(models.CompanyRepr).count(), 2)

        creprs = self.db.session.query(models.CompanyRepr).all()
        self.assertEqual(creprs[0].company, obj)
        self.assertEqual(creprs[1].company, obj)

        company = self.db.session.query(models.Company).one()
        self.assertEqual(len(company.reprs), 2)

    def test_update_related_model_by_updating_parent_model(self):
        data = {
            "reprs": [{"value": "TEST TEST"}, {"value": "TESTOWO"}], 
            "isin": "TEST", "name": "TEST"
        } 
        obj, errors = CompanySchema().load(data, session=self.db.session)
        self.db.session.add(obj)
        self.db.session.commit()

        crepr = obj.reprs[0]
        data = {
            "reprs": [{"id": crepr.id, "value": "NEW REPR #1"}], 
        }       
        obj, errors = CompanySchema().load(
            data, instance=obj,session=self.db.session, partial=True
        )
        self.db.session.commit()

        self.assertEqual(len(obj.reprs), 1)
        self.assertEqual(obj.reprs[0].value, "NEW REPR #1")

    def test_uniqness_is_not_validated_when_updating(self):
        company = models.Company(name="TEST", isin="#TEST")
        self.db.session.add(company)
        self.db.session.commit()

        data = {"name": "TEST", "ticker": "TEST", "isin": "#TEST"}
        obj, errors = CompanySchema().load(
            data, instance=company, session=self.db.session, partial=True
        )
        self.db.session.commit()

        self.assertFalse(errors)
        self.assertEqual(obj.ticker, "TEST")
        
    def test_id_field_in_reprs_with_empty_string_is_ignored(self):
        data = {
            "name": "TEST", "isin": "#TEST",
            "reprs": [{"value": "TEST REPR", "id": ""}]
        }
        
        obj, errors = CompanySchema().load(data, session=self.db.session)
        
        self.assertFalse(errors)


class FinancialStatementTypeReprSchemaTest(DbTestCase):

    def test_ftype_id_attribute_is_required(self):
        data = {"value": "Test Value", "lang": "PL"}
        
        obj, errors = FinancialStatementTypeReprSchema().load(
            data, session=self.db.session
        )
        
        self.assertTrue(errors)
        self.assertIn("ftype_id", errors)

    def test_ftype_has_to_exist_in_db(self):
        data = {"value": "Test Value", "ftype_id": 1, "lang": "PL"}
        
        obj, errors = FinancialStatementTypeReprSchema().load(
            data, session=self.db.session
        )
        
        self.assertTrue(errors)
        self.assertIn("ftype_id", errors)

    def test_load_creates_new_ftype_repr(self):
        ftype = models.FinancialStatementType(name="bls")
        self.db.session.add(ftype)
        self.db.session.commit()
        
        data = {"value": "NET PROFIT", "ftype_id": ftype.id, "lang": "PL"}
        obj, errors = FinancialStatementTypeReprSchema().load(
            data, session=self.db.session
        )
        self.db.session.add(obj)
        self.db.session.commit()
        
        ftype_repr = self.db.session.query(
            models.FinancialStatementTypeRepr
        ).first()
        self.assertIsNotNone(ftype_repr)
        self.assertEqual(ftype_repr.value, data["value"])
        self.assertEqual(ftype_repr.ftype, ftype)
        

class FinancialStatementTypeSchemaTest(DbTestCase):

    def test_name_is_required(self):
        data = {}

        obj, errors = FinancialStatementTypeSchema().load(
            data, session=self.db.session
        )

        self.assertTrue(errors)
        self.assertIn("name", errors)

    def test_name_has_to_be_unique(self):
        ftype = models.FinancialStatementType(name="bls")
        self.db.session.add(ftype)
        self.db.session.commit()

        data = {"name": "bls"}

        obj, errors = FinancialStatementTypeSchema().load(
            data, session=self.db.session
        )

        self.assertTrue(errors)
        self.assertIn("name", errors)   

    def test_load_creates_new_type(self):
        data = {"name": "bls"}

        obj, errors = FinancialStatementTypeSchema().load(
            data, session=self.db.session
        )

        self.db.session.add(obj)
        self.db.session.commit()

        rtype = self.db.session.query(models.FinancialStatementType).first()
        self.assertIsNotNone(rtype)
        self.assertEqual(rtype.name, data["name"])

    def test_deserialized_data_contains_recordtype_reprs(self):
        ftype = models.FinancialStatementType(name="bls")
        self.db.session.add(ftype)
        self.db.session.flush()
        self.db.session.add_all((
            models.FinancialStatementTypeRepr(value="Repr #1", ftype_id=ftype.id),
            models.FinancialStatementTypeRepr(value="Repr #2", ftype_id=ftype.id),
            models.FinancialStatementTypeRepr(value="Repr #3", ftype_id=ftype.id)
        ))
        self.db.session.commit()
        data = FinancialStatementTypeSchema().dump(ftype).data
        self.assertEqual(len(data["reprs"]), 3)
        values = [ item["value"] for item in data["reprs"] ]
        self.assertCountEqual(values, ["Repr #1", "Repr #2", "Repr #3"])
        
    def test_create_new_financial_type_with_reprs(self):
        data = {
            "name": "bls",
            "reprs": [{"value": "Repr #1"}, {"value": "Repr #2"}]
        }
        
        obj, errors = FinancialStatementTypeSchema().load(
            data=data, session=self.db.session
        )
        self.db.session.add(obj)
        self.db.session.commit()
        
        self.assertEqual(
            self.db.session.query(models.FinancialStatementType).count(), 
            1
        )
        self.assertEqual(
            self.db.session.query(models.FinancialStatementTypeRepr).count(), 
            2
        )
        
        ftype = self.db.session.query(models.FinancialStatementType).one()
        
        self.assertEqual(len(ftype.reprs), 2)
        self.assertIn(ftype.reprs[0].value, ["Repr #1", "Repr #2"])
        self.assertIn(ftype.reprs[1].value, ["Repr #1", "Repr #2"])
        
    def test_invalid_repr_makes_impossible_to_create_financial_type(self):
        data = {
            "name": "bls",
            "reprs": [{"value": "Repr #1"}, {"valu": "Repr #2"}]
        }
        
        obj, errors = FinancialStatementTypeSchema().load(
            data=data, session=self.db.session
        )

        self.assertTrue(errors)
        self.assertIn("reprs", errors)
        self.assertIn(1, errors["reprs"])
        self.assertEqual(
            self.db.session.query(models.FinancialStatementType).count(), 0
        )


class RecordTypeReprSchemaTest(DbTestCase):

    def test_rtype_id_attribute_is_required(self):
        data = {"value": "Test Value", "lang": "PL"}
        
        obj, errors = RecordTypeReprSchema().load(data, session=self.db.session)
        
        self.assertTrue(errors)
        self.assertIn("rtype_id", errors)

    def test_rtype_has_to_exist_in_db(self):
        data = {"value": "Test Value", "rtype_id": 1, "lang": "PL"}
        
        obj, errors = RecordTypeReprSchema().load(data, session=self.db.session)
        
        self.assertTrue(errors)
        self.assertIn("rtype_id", errors)

    def test_load_creates_new_recordtype_repr(self):
        ftype = models.FinancialStatementType(name="bls")
        rtype = models.RecordType(name="NETPROFIT", ftype=ftype)
        self.db.session.add(rtype)
        self.db.session.commit()
        
        data = {"value": "NET PROFIT", "rtype_id": rtype.id, "lang": "PL"}
        obj, errors = RecordTypeReprSchema().load(data, session=self.db.session)
        self.db.session.add(obj)
        self.db.session.commit()
        
        rtype_repr = self.db.session.query(models.RecordTypeRepr).first()
        self.assertIsNotNone(rtype_repr)
        self.assertEqual(rtype_repr.value, data["value"])
        self.assertEqual(rtype_repr.rtype, rtype)


class RecordTypeSchemaTest(DbTestCase):

    def test_name_attribute_is_required(self):
        data = {"ftype_id": "bls"}

        obj, errors = RecordTypeSchema().load(data, session=self.db.session)

        self.assertTrue(errors)
        self.assertIn("name", errors)

    def test_financial_statement_attribute_is_required(self):
        data = {"name": "TEST"}

        obj, errors = RecordTypeSchema().load(data, session=self.db.session)

        self.assertTrue(errors)
        self.assertIn("ftype_id", errors)

    def test_financial_statement_has_to_exist_in_db(self):
        data = {"name": "TEST", "ftype_id": 1}

        obj, errors = RecordTypeSchema().load(data, session=self.db.session)

        self.assertTrue(errors)
        self.assertIn("ftype_id", errors)

    def test_name_has_to_be_unique(self):
        ftype = create_ftype(self.db.session)
        self.db.session.add(models.RecordType(name="TEST", ftype=ftype))
        data = {"ftype_id": ftype.id, "name": "TEST"}
        obj, errors = RecordTypeSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("name", errors)

    def test_load_creates_new_recordtype(self):
        ftype = create_ftype(self.db.session)
        data = {"name": "TEST", "ftype_id": ftype.id}
        obj, errors = RecordTypeSchema().load(data, session=self.db.session)
        self.db.session.add(obj)
        self.db.session.commit()
        rtype = self.db.session.query(models.RecordType).first()
        self.assertIsNotNone(rtype)
        self.assertEqual(rtype.name, data["name"])
        self.assertEqual(rtype.ftype.id, data["ftype_id"])

    def test_deserialized_data_contains_recordtype_reprs(self):
        ftype = create_ftype(self.db.session)
        rtype = models.RecordType(name="TEST", ftype=ftype)
        self.db.session.add(rtype)
        self.db.session.flush()
        self.db.session.add_all((
            models.RecordTypeRepr(value="Repr #1", rtype_id=rtype.id),
            models.RecordTypeRepr(value="Repr #2", rtype_id=rtype.id),
            models.RecordTypeRepr(value="Repr #3", rtype_id=rtype.id)
        ))
        self.db.session.commit()
        data = RecordTypeSchema().dump(rtype).data
        self.assertEqual(len(data["reprs"]), 3)
        values = [ item["value"] for item in data["reprs"] ]
        self.assertCountEqual(values, ["Repr #1", "Repr #2", "Repr #3"])
        
    def test_create_new_record_type_with_reprs(self):
        ftype = create_ftype(self.db.session)
        data = {
            "name": "NETPROFIT", "ftype_id": ftype.id,
            "reprs": [{"value": "NET INCOME"}, {"value": "NET PROFIT"}]
        }
        
        obj, errors = RecordTypeSchema().load(data=data, session=self.db.session)
        self.db.session.add(obj)
        self.db.session.commit()
        
        self.assertEqual(self.db.session.query(models.RecordType).count(), 1)
        self.assertEqual(self.db.session.query(models.RecordTypeRepr).count(), 2)
        
        rtype = self.db.session.query(models.RecordType).one()
        
        self.assertEqual(len(rtype.reprs), 2)
        self.assertIn(rtype.reprs[0].value, ["NET INCOME", "NET PROFIT"])
        self.assertIn(rtype.reprs[1].value, ["NET INCOME", "NET PROFIT"])
        
    def test_invalid_repr_makes_impossible_to_create_record_type(self):
        ftype = create_ftype(self.db.session)
        data = {
            "name": "NETPROFIT", "ftype_id": ftype.id,
            # no value for repr
            "reprs": [{"lang": "PL"}, {"value": "NET PROFIT", "lang": "PL"}]
        } 
        
        obj, errors = RecordTypeSchema().load(data=data, session=self.db.session)

        self.assertTrue(errors)
        self.assertIn("reprs", errors)
        self.assertIn(0, errors["reprs"])
        self.assertEqual(self.db.session.query(models.RecordType).count(), 0)

    def test_empty_id_field_in_reprs_with_is_ignored(self):
        ftype = create_ftype(self.db.session)
        data = {
            "name": "NET PROFIT", "ftype_id": ftype.id,
            "reprs": [{"value": "TEST REPR", "id": "", "lang": "PL"}]
        }
        
        obj, errors = RecordTypeSchema().load(data, session=self.db.session)

        self.assertFalse(errors)
        
        
class RecordSchemaTest(DbTestCase):

    def test_company_id_attribute_is_required(self):
        data = {
            "value": 10, "rtype_id": 1, "timerange": 12,
            "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("company_id", errors)

    def test_rtype_id_attribute_is_required(self):
        data = {
            "value": 10, "company_id": 1, "timerange": 12,
            "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("rtype_id", errors)

    def test_value_attribute_is_required(self):
        data = {
            "rtype_id": 10, "company_id": 1, "timerange": 12,
            "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("value", errors)

    def test_timerange_attribute_is_required(self):
        data = {
            "rtype_id": 10, "company_id": 1,
            "timestamp": "2015-03-31", "value": 100,
        }
        obj, errors = RecordSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("timerange", errors)

    def test_timestamp_attribute_is_required(self):
        data = {
            "rtype_id": 10, "company_id": 1, "timerange": 12,
            "value": 120
        }
        obj, errors = RecordSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("timestamp", errors)

    def test_company_has_to_exist_in_db(self):
        data = {
            "rtype_id": 10, "company_id": 1, "timerange": 12,
            "value": 120, "rtype_id": 1, "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("company_id", errors)

    def test_rtype_has_to_exist_in_db(self):
        data = {
            "rtype_id": 10, "company_id": 1, "timerange": 12,
            "value": 120, "rtype_id": 1, "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("rtype_id", errors)

    def test_report_has_to_exist_in_db(self):
        data = {
            "rtype_id": 10, "company_id": 1, "timerange": 12,
            "value": 120, "rtype_id": 1, "timestamp": "2015-03-31",
            "report_id": 5
        }
        obj, errors = RecordSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("report_id", errors)

    def test_load_creates_new_record(self):
        company = models.Company(name="TEST", isin="TEST")
        ftype = create_ftype(self.db.session)
        rtype = models.RecordType(name="TEST", ftype=ftype, timeframe="pot")
        self.db.session.add_all((company, rtype))
        self.db.session.commit()
        data = {
            "rtype_id": 10, "company_id": company.id, "timerange": 12,
            "value": 120, "rtype_id": rtype.id, "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data, session=self.db.session)
        self.db.session.add(obj)
        self.db.session.commit()
        record = self.db.session.query(models.Record).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.value, data["value"])
        self.assertEqual(record.rtype, rtype)
        self.assertEqual(record.company, company)
        self.assertEqual(record.timerange, 12)
        self.assertEqual(record.timestamp, date(2015, 3, 31))

    def create_record(self, **kwargs):
        company = models.Company(name="TEST", isin="TEST")
        ftype = create_ftype(self.db.session)
        rtype = models.RecordType(
            name="TEST", ftype=ftype, 
            timeframe=kwargs.pop("timeframe", "pot")
        )
        self.db.session.add_all((company, rtype))
        self.db.session.flush()
        kwargs.update(dict(rtype=rtype, company=company))
        record = models.Record(**kwargs)
        self.db.session.add(record)
        self.db.session.commit()   
        return record

    def test_deserialized_data_contains_type_of_record(self):
        record = self.create_record(
            value=10, timerange=12, timestamp=datetime(2015, 3, 31)
        )

        data = RecordSchema().dump(record).data

        self.assertEqual(data["rtype"], "TEST")

    def test_combination_company_rtype_timestamp_and_timerange_is_unique(self):
        record = self.create_record(
            value=10, timerange=12, timestamp=datetime(2015, 3, 31),
            timeframe="pot"
        )
        data = {
            "rtype_id": record.rtype_id, "company_id": record.company_id, 
            "timerange": record.timerange, "value": 345, 
            "timestamp": "2015-03-31"
        }

        obj, errors = RecordSchema().load(data, session=self.db.session)

        self.assertTrue(errors)
        self.assertIn("record", errors)

    def test_timerange_of_pit_records_is_ignore_by_serializers(self):
        record = self.create_record(
            value=10, timerange=0, timeframe="pit", 
            timestamp=date(2015, 3, 31)
        )
        data = {
            "rtype_id": record.rtype_id, "company_id": record.company_id, 
            "timerange": 12, "value": 345, 
            "timestamp": "2015-03-31"
        }

        obj, errors = RecordSchema().load(data, session=self.db.session)

        # despite 'different' timeranges error is being risen
        self.assertTrue(errors)
        self.assertIn("record", errors)       

    def test_overridding_synthetic_records_doesnt_raise_errors(self):
        record = self.create_record(
            value=10, timerange=12, timeframe="pit", synthetic=True, 
            timestamp=date(2015, 3, 31)
        )

        data = {
            "rtype_id": record.rtype_id, "company_id": record.company_id, 
            "timerange": 0, "value": 345, 
            "timestamp": "2015-03-31"
        }

        obj, errors = RecordSchema().load(data, session=self.db.session)

        self.assertFalse(errors)
        self.assertEqual(obj.value, 345)

    def test_remove_synthetic_records_when_overridding(self):
        record = self.create_record(
            value=10, timerange=12, timeframe="pit", synthetic=True, 
            timestamp=date(2015, 3, 31)
        )

        data = {
            "rtype_id": record.rtype_id, "company_id": record.company_id, 
            "timerange": 0, "value": 345, 
            "timestamp": "2015-03-31"
        }

        obj, errors = RecordSchema().load(data, session=self.db.session) 
        
        self.db.session.add(obj)
        self.db.session.commit()   

        self.assertEqual(self.db.session.query(models.Record).count(), 1)

        record = self.db.session.query(models.Record).one()
        self.assertEqual(record.synthetic, False)
        self.assertEqual(record.value, 345)


class ReportSchemaTest(DbTestCase):

    def test_timerange_attribute_is_required(self):
        data = { "timestamp": "2015-03-31" }
        obj, errors = ReportSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("timerange", errors)

    def test_timestamp_attribute_is_required(self):
        data = { "timerange": 12 }
        obj, errors = ReportSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("timestamp", errors)
        
    def test_create_report_with_records(self):
        ftype = create_ftype(self.db.session)
        rtype = models.RecordType(name="NETPROFIT", ftype=ftype, timeframe="pot")
        self.db.session.add(rtype)
        company = models.Company(isin="#TEST", name="TEST")
        self.db.session.add(company)
        self.db.session.flush()
        
        data = {
            "timestamp": "2015-03-31", "timerange": 12,
            "records": [
                {
                    "value": 100, "timerange": 12, "timestamp": "2015-03-31", 
                    "rtype_id": rtype.id, "company_id": company.id
                },
                {
                    "value": 150, "timerange": 12, "timestamp": "2014-03-31",
                    "rtype_id": rtype.id, "company_id": company.id
                }
            ],
            "company_id": company.id
        }
        report, errors = ReportSchema().load(data, session=self.db.session)

        
        self.assertFalse(errors) 
        
        self.db.session.add(report)
        self.db.session.commit()
        
        records = self.db.session.query(models.Record).all()
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].company_id, company.id)
        self.assertEqual(records[0].rtype_id, rtype.id)
        self.assertEqual(records[0].value, 100)
        self.assertEqual(records[0].timerange, 12)
        self.assertEqual(records[1].company_id, company.id)
        self.assertEqual(records[1].rtype_id, rtype.id)
        self.assertEqual(records[1].value, 150)
        self.assertEqual(records[1].timerange, 12)
        
    def test_invalid_record_makes_impossible_to_create_report(self):
        ftype = create_ftype(self.db.session)
        rtype = models.RecordType(name="NETPROFIT", ftype=ftype)
        self.db.session.add(rtype)
        company = models.Company(isin="#TEST", name="TEST")
        self.db.session.add(company)
        self.db.session.flush()
        
        data = {
            "timestamp": "2015-03-31", "timerange": 12,
            "records": [
                {
                    "value": 100, "timerange": 12, "timestamp": "2015-03-31", 
                    "rtype_id": rtype.id + 1, #invalid rtype 
                    "company_id": company.id
                }
            ],
            "company_id": company.id
        }
        report, errors = ReportSchema().load(data, session=self.db.session) 
        
        self.assertTrue(errors)
        self.assertIn("records", errors)
        self.assertIn("rtype_id", errors["records"][0])

    def test_uniqueness_in_terms_of_timerange_timestamp_and_company(self):
        company = models.Company(isin="#TEST", name="TEST")
        self.db.session.add(company)
        report = models.Report(
            company=company, timerange=12, timestamp=date(2015, 3, 31)
        )
        self.db.session.add(report)
        self.db.session.flush()
        
        data = {
            "timestamp": datetime.strftime(report.timestamp, "%Y-%m-%d"), 
            "timerange": report.timerange,
            "company_id": report.company_id
        }
        report, errors = ReportSchema().load(data, session=self.db.session)

        self.assertTrue(errors)
        self.assertIn("report", errors)

        
def create_formula(session):
    ftype = create_ftype(session)
    total_assets = models.RecordType(name="TOTAL_ASSETS", ftype=ftype)
    current_assets = models.RecordType(name="CURRENT_ASSETS", ftype=ftype)
    fixed_assets = models.RecordType(name="FIXED_ASSETS", ftype=ftype)
    session.add_all((total_assets, current_assets, fixed_assets))
    session.flush()    
    
    formula = models.RecordFormula(rtype=total_assets)
    formula.add_component(rtype=current_assets, sign=1)
    formula.add_component(rtype=fixed_assets, sign=1)
    session.add(formula)
    session.commit()
    
    return formula
        
        
class RecordFormulaTest(DbTestCase):
    
    def test_rtype_attribute_is_required(self):
        data = {}
        obj, errors = RecordFormulaSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("rtype_id", errors)

    def test_rtype_has_to_exist_in_db(self):
        data = {"rtype_id": 10}
        obj, errors = RecordFormulaSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("rtype_id", errors)
        
    def test_load_creates_new_formula(self):
        ftype = create_ftype(self.db.session)
        rtype = models.RecordType(name="TEST TYPE", ftype=ftype)
        self.db.session.add(rtype)
        self.db.session.flush()
        
        data = {"rtype_id": rtype.id}
        obj, errors = RecordFormulaSchema().load(data, session=self.db.session)
        self.db.session.add(obj)
        self.db.session.commit()
        
        formula = self.db.session.query(models.RecordFormula).one()
        self.assertEqual(formula.rtype_id, rtype.id)

    def test_deserialized_formula_contains_list_of_components(self):
        formula = create_formula(self.db.session)
        data = RecordFormulaSchema().dump(formula).data
        
        self.assertEqual(len(data["components"]), 2)
        values = [ item["rtype"] for item in data["components"] ]
        self.assertCountEqual(values, ["CURRENT_ASSETS", "FIXED_ASSETS"])
        
        
class FormulaComponentTest(DbTestCase):
    
    def test_rtype_attribute_is_required(self):
        data = {}
        obj, errors = FormulaComponentSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("rtype_id", errors)
        
    def test_rtype_has_to_exist_in_db(self):
        formula = create_formula(self.db.session)
        data = {"rtype_id": 10, "formula_id": formula.id}
        obj, errors = FormulaComponentSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("rtype_id", errors)
        
    def test_formula_attribute_is_required(self):
        data = {}
        obj, errors = FormulaComponentSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("formula_id", errors)
        
    def test_formula_has_to_exist_in_db(self):
        data = {"formula_id": 10}
        obj, errors = FormulaComponentSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("formula_id", errors)
        
    def test_deserialized_data_contains_data_of_record_type(self):
        formula = create_formula(self.db.session)
        component = formula.components[0]
        data = FormulaComponentSchema().dump(component).data
        self.assertIn("rtype", data)
        self.assertEqual(data["rtype"], component.rtype.name)