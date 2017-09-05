from datetime import datetime
import json

from flask import url_for

from app import db
from app.rapi import api
from db.serializers import DatetimeEncoder
from db.models import (
    Company, Report, CompanyRepr, RecordType, RecordTypeRepr, Record
)
from app.models import Permission, Role, User, DBRequest

from tests.app import AppTestCase, create_and_login_user


class TestCompanyDetail(AppTestCase):

    @create_and_login_user()
    def test_get_request_returns_company_data(self):
        comp = Company.create(db.session, name="TEST1", isin="#TEST1")
        db.session.commit()
        response = self.client.get(url_for("rapi.company_detail", id=comp.id))
        data = response.json
        self.assertEqual(data["name"], comp.name)
        self.assertEqual(data["isin"], comp.isin)

    @create_and_login_user()
    def test_get_request_returns_404_when_company_does_not_exist(self):
        db.session.commit()
        response = self.client.get(url_for("rapi.company_detail", id=1))       
        self.assertEqual(response.status_code, 404)

    @create_and_login_user(pass_user=True)
    def test_delete_request_creates_dbrequest(self, user):
        comp = Company.create(db.session, name="TEST1", isin="#TEST1")
        db.session.commit() 
        response = self.client.delete(url_for("rapi.company_detail", id=comp.id))
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        dbrequest = db.session.query(DBRequest).first()
        data = json.loads(dbrequest.data)
        self.assertEqual(dbrequest.action, "delete")
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(data["id"], comp.id)

    @create_and_login_user(pass_user=True)
    def test_put_request_creates_dbrequest(self, user):
        comp = Company.create(db.session, name="TEST1", isin="#TEST1")
        db.session.commit()
        response = self.client.put(
            url_for("rapi.company_detail", id=comp.id),
            data=json.dumps(
                {"name": "NEW NAME", "ticker": "HEJ"},
                cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        dbrequest = db.session.query(DBRequest).first()
        data = json.loads(dbrequest.data)
        self.assertEqual(dbrequest.action, "update")
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(data["id"], comp.id)
        self.assertEqual(data["name"], "NEW NAME")
        self.assertEqual(data["ticker"], "HEJ")

    @create_and_login_user(role_name="Visitor")
    def test_user_without_modify_permission_cannot_update_data(self):
        comp = Company.create(db.session, name="TEST1", isin="#TEST1")
        db.session.commit()
        response = self.client.put(
            url_for("rapi.company_detail", id=comp.id),
            data=json.dumps(
                {"name": "NEW NAME", "ticker": "HEJ"},
                cls=DatetimeEncoder
            ),
            content_type="application/json"
        ) 
        self.assertEqual(response.status_code, 401)

    # @create_and_login_user()
    # def test_raises_400_when_updating_with_not_unique_isin(self):
    #     Company.create(db.session, name="TEST1", isin="#TEST2")
    #     comp = Company.create(db.session, name="TEST1", isin="#TEST1")
    #     db.session.commit()
    #     response = self.client.put(
    #         url_for("rapi.company", id=comp.id),
    #         data=json.dumps(
    #             {"name": "NEW NAME", "isin": "#TEST2"},
    #             cls=DatetimeEncoder
    #         ),
    #         content_type="application/json"
    #     )
    #     self.assertEqual(response.status_code, 400)
        
    @create_and_login_user()
    def test_for_returning_only_request_fields(self):
        comp = Company.create(db.session, name="TEST1", isin="#TEST2")
        db.session.commit()
        response = self.client.get(
            url_for("rapi.company_detail", id=comp.id),
            query_string={"fields": "name, id"}
        )
        data = response.json
        self.assertEqual(set(data.keys()), set(("name", "id")))