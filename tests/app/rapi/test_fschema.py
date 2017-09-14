from datetime import datetime, date
import json

from flask import url_for

from app import db
import db.models as models

from tests.app import AppTestCase, create_and_login_user
from tests.app.utils import *


def create_schema_with_records():
    company = create_company(name="Test", isin="#TEST")
    ta, ca, fa = create_rtypes()
    records = create_records([
        (company, ta, 0, date(2015, 12, 31), 100),
        (company, fa, 0, date(2015, 12, 31), 50)
    ])  
    db.session.add_all(records)
    schema = FinancialStatementSchema()
    schema.append_rtype(fa, 0)
    schema.append_rtype(ca, 1)
    schema.append_rtype(ta, 2)
    db.session.add(schema)
    db.session.commit()
    return schema


class TestListView(AppTestCase):

    @create_and_login_user()
    def test_get_request_returns_json_response(self):
        response = self.client.get(url_for("rapi.fschema_list"))
        self.assertEqual(response.content_type, "application/json")

    @create_and_login_user()
    def test_get_request_returns_list_of_fschemas(self):
        company = create_company(name="Test", isin="#TEST")
        ta, ca, fa = create_rtypes()
        schema = models.FinancialStatementSchema()
        schema.append_rtype(fa, 0)
        schema.append_rtype(ca, 1)
        schema.append_rtype(ta, 2)
        db.session.add(schema)
        db.session.commit()

        schema2 = models.FinancialStatementSchema()
        schema2.append_rtype(fa, 0)
        schema2.append_rtype(ca, 1)
        db.session.add(schema2)       
        db.session.commit()

        response = self.client.get(url_for("rapi.fschema_list"))
        
        data = response.json["results"]
        self.assertEqual(len(data), 2)


class TestDetailView(AppTestCase):

    @create_and_login_user()
    def test_get_request_returns_json_response(self):
        schema = create_schema_with_records()
        response = self.client.get(url_for("rapi.fschema_detail", id=schema.id))
        self.assertEqual(response.content_type, "application/json")

    @create_and_login_user()
    def test_get_request_returns_404_when_company_does_not_exist(self):
        response = self.client.get(url_for("rapi.fschema_detail", id=1))       
        self.assertEqual(response.status_code, 404)


class TestRecordsView(AppTestCase):

    @create_and_login_user()
    def test_get_request_returns_json_response(self):
        schema = create_schema_with_records()
        response = self.client.get(
            url_for("rapi.fschema_records", id=schema.id),
            query_string={
                "company": db.session.query(Company).first().id,
                "timerange": 0
            },
        )
        self.assertEqual(response.content_type, "application/json")

    @create_and_login_user()
    def test_get_request_returns_proper_records(self):
        schema = create_schema_with_records()

        response = self.client.get(
            url_for("rapi.fschema_records", id=schema.id),
            query_string={
                "company": db.session.query(Company).first().id,
                "timerange": 0
            },
        )

        data = response.json["records"]
        self.assertEqual(len(data), 2)

        rtypes = [ item["rtype"] for item in data ]
        self.assertCountEqual(rtypes, ["TOTAL_ASSETS", "FIXED_ASSETS"])

    @create_and_login_user()
    def test_get_request_returns_formatted_data(self):
        schema = create_schema_with_records()

        response = self.client.get(
            url_for("rapi.fschema_records", id=schema.id),
            query_string={
                "company": db.session.query(Company).first().id,
                "timerange": 0, "format": "T"
            },
        )

        self.assertIn("company", response.json)
        self.assertIn("timerange", response.json)

        self.assertEqual(response.json["count"], 2)

    @create_and_login_user()
    def test_get_request_raises_400_when_no_company(self):
        schema = create_schema_with_records()

        response = self.client.get(
            url_for("rapi.fschema_records", id=schema.id)
        )

        self.assertEqual(response.status_code, 400)