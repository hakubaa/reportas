import unittest
import unittest.mock as mock
from datetime import datetime

from flask import url_for

from tests.app import AppTestCase
from app import db
from app.rapi.schemas import *  
import db.models as models


class CompanyReprSchemaTest(AppTestCase):
    models = [models.Company, models.CompanyRepr]

    def test_company_id_attribute_is_required(self):
        data = {"value": "Test Value"}
        obj, errors = CompanyReprSchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("company_id", errors)

    def test_company_has_to_exist_in_db(self):
        data = {"value": "Test Value", "company_id": 1}
        obj, errors = CompanyReprSchema().load(data, session=db.session)
        self.assertIsNotNone(errors)
        self.assertIn("company_id", errors)

    def test_load_creates_new_companyrepr(self):
        company = models.Company(name="TEST", isin="#TEST")
        db.session.add(company)
        db.session.commit()
        data = {"value": "Test Value", "company_id": company.id}
        obj, errors = CompanyReprSchema().load(data, session=db.session)
        db.session.add(obj)
        db.session.commit()
        crepr = db.session.query(models.CompanyRepr).first()
        self.assertIsNotNone(crepr)
        self.assertEqual(crepr.value, data["value"])
        self.assertEqual(crepr.company, company)


class CompanySchemaTest(AppTestCase):
    models = [models.Company, models.CompanyRepr]

    def test_name_attribute_is_required(self):
        data = {"isin": "#test"}
        obj, errors = CompanySchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("name", errors)

    def test_isin_attribute_is_required(self):
        data = {"name": "test"}
        obj, errors = CompanySchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("isin", errors)

    def test_isin_has_to_be_unique(self):
        db.session.add(models.Company(name="TEST", isin="#TEST"))
        data = {"isin": "#TEST", "name": "Company"}
        obj, errors = CompanySchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("isin", errors)

    def test_load_creates_new_company(self):
        data = {"name": "Test Name", "isin": "#ISIN"}
        obj, errors = CompanySchema().load(data, session=db.session)
        db.session.add(obj)
        db.session.commit()
        company = db.session.query(models.Company).first()
        self.assertIsNotNone(company)
        self.assertEqual(company.name, data["name"])
        self.assertEqual(company.isin, data["isin"])

    def test_deserialized_data_contains_hyperlinks(self):
        company = models.Company(name="TEST", isin="#TEST")
        db.session.add(company)
        db.session.commit()
        data = CompanySchema().dump(company).data
        self.assertEqual(
            data["reports"], url_for("rapi.company_report_list", id=company.id)
        )
        self.assertEqual(
            data["records"], url_for("rapi.company_record_list", id=company.id)
        )

    def test_deserialized_data_contains_company_reprs(self):
        company = models.Company(name="TEST", isin="#TEST")
        db.session.add(company)
        db.session.flush()
        db.session.add_all((
            models.CompanyRepr(value="Repr #1", company_id=company.id),
            models.CompanyRepr(value="Repr #2", company_id=company.id),
            models.CompanyRepr(value="Repr #3", company_id=company.id)
        ))
        db.session.commit()
        data = CompanySchema().dump(company).data
        self.assertEqual(len(data["reprs"]), 3)
        values = [ item["value"] for item in data["reprs"] ]
        self.assertCountEqual(values, ["Repr #1", "Repr #2", "Repr #3"])


class CompanySimpleSchemaTest(AppTestCase):
    models = [models.Company, models.CompanyRepr]

    def test_deserialized_data_contains_uri_to_full_version(self):
        company = models.Company(name="TEST", isin="#TEST")
        db.session.add(company)
        db.session.commit()
        data = CompanySimpleSchema().dump(company).data
        self.assertEqual(
            data["uri"], url_for("rapi.company_detail", id=company.id)
        )


class RecordTypeSchemaTest(AppTestCase):
    models = [
        models.RecordType, models.RecordTypeRepr, models.Record,
        models.Company, models.CompanyRepr
    ]

    def test_name_attribute_is_required(self):
        data = {"statement": "bls"}
        obj, errors = RecordTypeSchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("name", errors)

    def test_statement_attribute_is_required(self):
        data = {"name": "TEST"}
        obj, errors = RecordTypeSchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("statement", errors)

    def test_name_has_to_be_unique(self):
        db.session.add(models.RecordType(name="TEST", statement="bls"))
        data = {"statement": "nls", "name": "TEST"}
        obj, errors = RecordTypeSchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("name", errors)

    def test_load_creates_new_recordtype(self):
        data = {"name": "TEST", "statement": "bls"}
        obj, errors = RecordTypeSchema().load(data)
        db.session.add(obj)
        db.session.commit()
        rtype = db.session.query(models.RecordType).first()
        self.assertIsNotNone(rtype)
        self.assertEqual(rtype.name, data["name"])
        self.assertEqual(rtype.statement, data["statement"])

    def test_statement_has_to_be_one_of_nls_bls_cls(self):
        data = {"statement": "nie", "name": "TEST"}
        obj, errors = RecordTypeSchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("statement", errors)

    def test_deserialized_data_contains_recordtype_reprs(self):
        rtype = models.RecordType(name="TEST", statement="bls")
        db.session.add(rtype)
        db.session.flush()
        db.session.add_all((
            models.RecordTypeRepr(value="Repr #1", rtype_id=rtype.id),
            models.RecordTypeRepr(value="Repr #2", rtype_id=rtype.id),
            models.RecordTypeRepr(value="Repr #3", rtype_id=rtype.id)
        ))
        db.session.commit()
        data = RecordTypeSchema().dump(rtype).data
        self.assertEqual(len(data["reprs"]), 3)
        values = [ item["value"] for item in data["reprs"] ]
        self.assertCountEqual(values, ["Repr #1", "Repr #2", "Repr #3"])


class RecordTypeSimpleSchemaTest(AppTestCase):
    models = [
        models.RecordType, models.RecordTypeRepr, models.Record,
        models.Company, models.CompanyRepr
    ]

    def test_deserialized_data_contains_uri_to_full_version(self):
        rtype = models.RecordType(name="TEST", statement="bls")
        db.session.add(rtype)
        db.session.commit()
        data = RecordTypeSimpleSchema().dump(rtype).data
        self.assertEqual(
            data["uri"], url_for("rapi.rtype_detail", id=rtype.id)
        )


class RecordSchemaTest(AppTestCase):
    models = [
        models.RecordType, models.RecordTypeRepr, models.Record,
        models.Company, models.CompanyRepr, models.Report
    ]

    def test_company_id_attribute_is_required(self):
        data = {
            "value": 10, "rtype_id": 1, "timerange": 12,
            "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("company_id", errors)

    def test_rtype_id_attribute_is_required(self):
        data = {
            "value": 10, "company_id": 1, "timerange": 12,
            "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("rtype_id", errors)

    def test_value_attribute_is_required(self):
        data = {
            "rtype_id": 10, "company_id": 1, "timerange": 12,
            "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("value", errors)

    def test_timerange_attribute_is_required(self):
        data = {
            "rtype_id": 10, "company_id": 1,
            "timestamp": "2015-03-31", "value": 100,
        }
        obj, errors = RecordSchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("timerange", errors)

    def test_timestamp_attribute_is_required(self):
        data = {
            "rtype_id": 10, "company_id": 1, "timerange": 12,
            "value": 120
        }
        obj, errors = RecordSchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("timestamp", errors)

    def test_company_has_to_exist_in_db(self):
        data = {
            "rtype_id": 10, "company_id": 1, "timerange": 12,
            "value": 120, "rtype_id": 1, "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data, session=db.session)
        self.assertIsNotNone(errors)
        self.assertIn("company_id", errors)

    def test_rtype_has_to_exist_in_db(self):
        data = {
            "rtype_id": 10, "company_id": 1, "timerange": 12,
            "value": 120, "rtype_id": 1, "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data, session=db.session)
        self.assertIsNotNone(errors)
        self.assertIn("rtype_id", errors)

    def test_report_has_to_exist_in_db(self):
        data = {
            "rtype_id": 10, "company_id": 1, "timerange": 12,
            "value": 120, "rtype_id": 1, "timestamp": "2015-03-31",
            "report_id": 5
        }
        obj, errors = RecordSchema().load(data, session=db.session)
        self.assertIsNotNone(errors)
        self.assertIn("report_id", errors)

    def test_load_creates_new_record(self):
        company = models.Company(name="TEST", isin="TEST")
        rtype = models.RecordType(name="TEST", statement="bls")
        db.session.add_all((company, rtype))
        db.session.commit()
        data = {
            "rtype_id": 10, "company_id": company.id, "timerange": 12,
            "value": 120, "rtype_id": rtype.id, "timestamp": "2015-03-31"
        }
        obj, errors = RecordSchema().load(data, session=db.session)
        db.session.add(obj)
        db.session.commit()
        record = db.session.query(models.Record).first()
        self.assertIsNotNone(record)
        self.assertEqual(record.value, data["value"])
        self.assertEqual(record.rtype, rtype)
        self.assertEqual(record.company, company)
        self.assertEqual(record.timerange, 12)
        self.assertEqual(record.timestamp, datetime(2015, 3, 31))

    def test_deserialized_data_contains_type_of_record(self):
        company = models.Company(name="TEST", isin="TEST")
        rtype = models.RecordType(name="TEST", statement="bls")
        db.session.add_all((company, rtype))
        db.session.flush()
        record = models.Record(
            value=10, timerange=12, company=company, rtype=rtype, 
            timestamp=datetime(2015, 3, 31)
        )
        db.session.add(record)
        db.session.commit()
        data = RecordSchema().dump(record).data
        self.assertEqual(data["rtype"]["name"], "TEST")

    def test_deserialized_data_contains_hyperlinks(self):
        company = models.Company(name="TEST", isin="TEST")
        rtype = models.RecordType(name="TEST", statement="bls")
        report = models.Report(timerange=12, timestamp=datetime(2012, 12, 31))
        db.session.add_all((company, rtype, report))
        db.session.flush()
        record = models.Record(
            value=10, timerange=12, company=company, rtype=rtype, 
            timestamp=datetime(2015, 3, 31), report=report
        )
        db.session.add(record)
        db.session.commit()
        data = RecordSchema().dump(record).data
        # self.assertEqual(
        #     data["report"], url_for("rapi.report_detail", id=report.id)
        # )
        self.assertEqual(
            data["company"], url_for("rapi.company_detail", id=company.id)
        )

class ReportSchemaTest(AppTestCase):
    models = [
        models.RecordType, models.RecordTypeRepr, models.Record,
        models.Company, models.CompanyRepr, models.Report
    ]

    def test_timerange_attribute_is_required(self):
        data = { "timestamp": "2015-03-31" }
        obj, errors = ReportSchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("timerange", errors)

    def test_timestamp_attribute_is_required(self):
        data = { "timerange": 12 }
        obj, errors = ReportSchema().load(data)
        self.assertIsNotNone(errors)
        self.assertIn("timestamp", errors)

    def test_deserialized_data_contains_hyperlinks(self):
        company = models.Company(name="TEST", isin="#TEST")
        db.session.add(company)
        db.session.commit()
        report = models.Report(timerange=12, timestamp=datetime(2015, 3, 31),
                               company=company)
        db.session.add(report)
        db.session.commit()
        data = ReportSchema().dump(report).data
        self.assertEqual(
            data["company"], url_for("rapi.company_detail", id=company.id)
        )
        self.assertEqual(
            data["records"], url_for("rapi.report_record_list", id=report.id)
        )