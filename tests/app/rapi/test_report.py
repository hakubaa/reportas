from datetime import datetime, date
import json

from flask import url_for
import dateutil

from app import db
from app.rapi import api
from app.rapi.util import DatetimeEncoder
import db.models as models
from db.models import Company, Report
from app.models import Permission, Role, User, DBRequest

from tests.app import AppTestCase, create_and_login_user


class TestListView(AppTestCase):

    def create_fake_company(self, name="TEST", isin="#TEST"):
        company = Company(name=name, isin=isin)
        db.session.add(company)
        db.session.commit()
        return company

    @create_and_login_user()
    def test_get_request_returns_json_response(self):
        response = self.client.get(url_for("rapi.report_list"))
        self.assertEqual(response.content_type, "application/json")

    @create_and_login_user()
    def test_get_request_returns_list_of_reports(self):
        company = self.create_fake_company()
        report1 = Report.create(
            db.session, timerange=3, company_id=company.id,
            timestamp=datetime(2015, 3, 31)
        )
        report2 = Report.create(
            db.session, timerange=3, company_id=company.id,
            timestamp=datetime(2016, 3, 31)
        )
        db.session.commit()
        response = self.client.get(url_for("rapi.report_list"))
        data = response.json["results"]
        self.assertEqual(len(data), 2)

    @create_and_login_user()
    def test_get_request_returns_report_data(self):
        company = self.create_fake_company()
        report = Report.create(
            db.session, timerange=3, company_id=company.id,
            timestamp=date(2015, 3, 31)
        )
        db.session.commit()
        response = self.client.get(url_for("rapi.report_list"))
        data = response.json["results"][0]
        self.assertEqual(
            data["timestamp"], 
            datetime.strftime(report.timestamp, "%Y-%m-%d")
        )
        self.assertEqual(data["timerange"], report.timerange)

    @create_and_login_user()
    def test_get_request_returns_hyperlink_to_records(self):
        company = self.create_fake_company()
        report = Report.create(
            db.session, timerange=3, company_id=company.id,
            timestamp=datetime(2015, 3, 31)
        )
        db.session.commit()
        response = self.client.get(url_for("rapi.report_list"))
        data = response.json["results"][0]
        self.assertIsNotNone(data["records"])
        self.assertEqual(
            data["records"], url_for("rapi.report_record_list", id=report.id)
        )

    @create_and_login_user(role_name="User")
    def test_post_request_creates_dbrequest(self):
        company = self.create_fake_company()
        response = self.client.post(
            url_for("rapi.report_list"),
            data = json.dumps(
                {
                    "timestamp": "2015-03-31", "timerange": 12, 
                    "company_id": company.id
                },
                cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        self.assertEqual(db.session.query(DBRequest).count(), 1)

    @create_and_login_user(pass_user=True, role_name="User")
    def test_post_request_creates_dbrequest_with_proper_data(self, user):
        company = self.create_fake_company()
        response = self.client.post(
            url_for("rapi.report_list"),
            data = json.dumps(
                {
                    "timestamp": "2015-03-31", "timerange": 12, 
                    "company_id": company.id
                },
                cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).first()
        data = json.loads(dbrequest.data)
        self.assertEqual(data["timerange"], 12)
        self.assertEqual(data["timestamp"], "2015-03-31")
        self.assertEqual(data["company_id"], company.id) 
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "create")
        self.assertEqual(dbrequest.model, "Report")