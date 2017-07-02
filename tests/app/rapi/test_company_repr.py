from datetime import datetime
import json

from flask import url_for

from app import db
from app.rapi import api
from app.rapi.util import DatetimeEncoder
from db.models import (
    Company, Report, CompanyRepr, RecordType, RecordTypeRepr, Record
)
from app.models import Permission, Role, User, DBRequest

from tests.app import AppTestCase, create_and_login_user


def create_company_with_reprs(n=2, name="TEST"):
    company = Company.create(db.session, name=name, isin="#" + name)
    db.session.add(company)
    for i in range(n):
        company.reprs.append(
            CompanyRepr.create(
                db.session, value="Company Test Repr. #{}".format(i)
            )
        )
    db.session.commit()
    return company


class TestListView(AppTestCase):

    @create_and_login_user()
    def test_for_retrieving_list_of_reprs(self):
        company = create_company_with_reprs(n=10)
        response = self.client.get(
            url_for("rapi.company_repr_list", id=company.id)
        )
        data = response.json
        self.assertEqual(data["count"], 10)

    @create_and_login_user()
    def test_get_request_returns_correct_data(self):
        company = create_company_with_reprs(n=1)
        create_company_with_reprs(n=10, name="FAKE")
        response = self.client.get(
            url_for("rapi.company_repr_list", id=company.id)
        )
        data = response.json["results"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["value"], company.reprs[0].value)

    @create_and_login_user(pass_user=True)
    def test_post_request_creates_dbrequest(self, user):
        company = create_company_with_reprs(n=0)
        response = self.client.post(
            url_for("rapi.company_repr_list", id=company.id),
            data=json.dumps(
                {"value": "Company Repr"}, cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        data = json.loads(dbrequest.data)
        self.assertEqual(data["value"], "Company Repr") 
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "create")
        self.assertEqual(dbrequest.model, "CompanyRepr")       

    @create_and_login_user(pass_user=True)
    def test_company_id_set_by_default_in_dbrequest(self, user):
        company = create_company_with_reprs(n=0)
        response = self.client.post(
            url_for("rapi.company_repr_list", id=company.id),
            data=json.dumps(
                {"value": "Company Repr", "company": 123}, cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        data = json.loads(dbrequest.data)
        self.assertEqual(data["company_id"], company.id)


class TestDetailView(AppTestCase):

    @create_and_login_user()
    def test_get_request_returns_detail_of_repr(self):
        company = create_company_with_reprs(n=1)
        response = self.client.get(
            url_for("rapi.company_repr_detail", id=company.id, 
                    rid=company.reprs[0].id)
        )
        data = response.json
        self.assertEqual(data["value"], company.reprs[0].value)

    @create_and_login_user(pass_user=True)
    def test_put_request_creates_dbrequet(self, user):
        company = create_company_with_reprs(n=1)
        response = self.client.put(
            url_for("rapi.company_repr_detail", id=company.id, 
                    rid=company.reprs[0].id),
            data=json.dumps(
                {"value": "New Test Repr"},
                cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        data = json.loads(dbrequest.data)
        self.assertEqual(dbrequest.action, "update")
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(data["id"], company.reprs[0].id)
        self.assertEqual(data["company_id"], company.id)
        self.assertEqual(data["value"], "New Test Repr")

    @create_and_login_user(pass_user=True)
    def test_delete_request_deletes_repr(self, user):
        company = create_company_with_reprs(n=1)
        response = self.client.delete(
            url_for("rapi.company_repr_detail", id=company.id, 
                    rid=company.reprs[0].id),
        )
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        self.assertEqual(dbrequest.action, "delete")
        self.assertEqual(dbrequest.user, user)