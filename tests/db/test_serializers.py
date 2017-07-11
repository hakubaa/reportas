import unittest
import unittest.mock as mock
from datetime import datetime

from tests.db import DbTestCase
from db.serializers import *  
import db.models as models


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


class RecordTypeSchemaTest(DbTestCase):

    def test_name_attribute_is_required(self):
        data = {"statement": "bls"}
        obj, errors = RecordTypeSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("name", errors)

    def test_statement_attribute_is_required(self):
        data = {"name": "TEST"}
        obj, errors = RecordTypeSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("statement", errors)

    def test_name_has_to_be_unique(self):
        self.db.session.add(models.RecordType(name="TEST", statement="bls"))
        data = {"statement": "nls", "name": "TEST"}
        obj, errors = RecordTypeSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("name", errors)

    def test_load_creates_new_recordtype(self):
        data = {"name": "TEST", "statement": "bls"}
        obj, errors = RecordTypeSchema().load(data, session=self.db.session)
        self.db.session.add(obj)
        self.db.session.commit()
        rtype = self.db.session.query(models.RecordType).first()
        self.assertIsNotNone(rtype)
        self.assertEqual(rtype.name, data["name"])
        self.assertEqual(rtype.statement, data["statement"])

    def test_statement_has_to_be_one_of_nls_bls_cls(self):
        data = {"statement": "nie", "name": "TEST"}
        obj, errors = RecordTypeSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("statement", errors)

    def test_deserialized_data_contains_recordtype_reprs(self):
        rtype = models.RecordType(name="TEST", statement="bls")
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
        rtype = models.RecordType(name="TEST", statement="bls")
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
        self.assertEqual(record.timestamp, datetime(2015, 3, 31))

    def test_deserialized_data_contains_type_of_record(self):
        company = models.Company(name="TEST", isin="TEST")
        rtype = models.RecordType(name="TEST", statement="bls")
        self.db.session.add_all((company, rtype))
        self.db.session.flush()
        record = models.Record(
            value=10, timerange=12, company=company, rtype=rtype, 
            timestamp=datetime(2015, 3, 31)
        )
        self.db.session.add(record)
        self.db.session.commit()
        data = RecordSchema().dump(record).data
        self.assertEqual(data["rtype"]["name"], "TEST")

    def test_combination_company_rtype_timestamp_and_timerange_is_unique(self):
        company = models.Company(name="TEST", isin="TEST")
        rtype = models.RecordType(name="TEST", statement="bls")
        self.db.session.add_all((company, rtype))
        self.db.session.flush()
        record = models.Record(
            value=10, timerange=12, company=company, rtype=rtype, 
            timestamp=datetime(2015, 3, 31)
        )
        self.db.session.add(record)
        self.db.session.commit()
        data = {
            "rtype_id": record.rtype_id, "company_id": record.company_id, 
            "timerange": record.timerange, "value": 345, 
            "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data, session=self.db.session)
        self.assertTrue(errors)
        self.assertIn("record", errors)


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


def create_formula(session):
    total_assets = models.RecordType(name="TOTAL_ASSETS", statement="bls")
    current_assets = models.RecordType(name="CURRENT_ASSETS", statement="bls")
    fixed_assets = models.RecordType(name="FIXED_ASSETS", statement="bls")
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
        rtype = models.RecordType(name="TEST TYPE", statement="nls")
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