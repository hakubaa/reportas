import unittest
import unittest.mock as mock
from datetime import datetime

from flask import url_for

from tests.app import AppTestCase
from app import db
from app.rapi.serializers import *  
import db.models as models


def create_ftype(name="bls"):
    return models.FinancialStatement.create(db.session, name=name)


class CompanySchemaTest(AppTestCase):

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


class CompanySimpleSchemaTest(AppTestCase):

    def test_deserialized_data_contains_uri_to_full_version(self):
        company = models.Company(name="TEST", isin="#TEST")
        db.session.add(company)
        db.session.commit()
        data = CompanySimpleSchema().dump(company).data
        self.assertEqual(
            data["uri"], url_for("rapi.company_detail", id=company.id)
        )


class RecordTypeSimpleSchemaTest(AppTestCase):

    def test_deserialized_data_contains_uri_to_full_version(self):
        rtype = models.RecordType(
            name="TEST", ftype=create_ftype("bls"),
            timeframe=models.RecordType.PIT
        )
        db.session.add(rtype)
        db.session.commit()
        data = RecordTypeSimpleSchema().dump(rtype).data
        self.assertEqual(
            data["uri"], url_for("rapi.rtype_detail", id=rtype.id)
        )


class RecordSchemaTest(AppTestCase):

    def test_deserialized_data_contains_hyperlinks(self):
        company = models.Company(name="TEST", isin="TEST")
        rtype = models.RecordType(
            name="TEST", ftype=create_ftype("bls"),
            timeframe=models.RecordType.PIT
        )
        report = models.Report(
            timerange=12, timestamp=datetime(2012, 12, 31), company=company
        )
        db.session.add_all((company, rtype, report))
        db.session.flush()
        record = models.Record(
            value=10, timerange=12, company=company, rtype=rtype, 
            timestamp=datetime(2015, 3, 31), report=report
        )
        db.session.add(record)
        db.session.commit()
        data = RecordSchema().dump(record).data
        self.assertEqual(
            data["report"], url_for("rapi.report_detail", id=report.id)
        )
        self.assertEqual(
            data["company"], url_for("rapi.company_detail", id=company.id)
        )


class ReportSchemaTest(AppTestCase):

    def test_deserialized_data_contains_hyperlinks(self):
        company = models.Company(name="TEST", isin="#TEST")
        db.session.add(company)
        db.session.commit()
        report = models.Report(
            timerange=12, timestamp=datetime(2015, 3, 31), company=company
        )
        db.session.add(report)
        db.session.commit()
        data = ReportSchema().dump(report).data
        self.assertEqual(
            data["company"], url_for("rapi.company_detail", id=company.id)
        )
        self.assertEqual(
            data["records"], url_for("rapi.report_record_list", id=report.id)
        )