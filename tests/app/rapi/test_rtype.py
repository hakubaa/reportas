from datetime import datetime
import json

from flask import url_for

from app import db
from app.rapi import api
from db.serializers import DatetimeEncoder
from db.models import (
    Company, Report, CompanyRepr, RecordType, RecordTypeRepr, Record,
    FinancialStatement
)
from app.models import Permission, Role, User, DBRequest

from tests.app import AppTestCase, create_and_login_user


def create_ftype(name="bls"):
    return FinancialStatement.create(db.session, name=name)


class TestRecordTypeList(AppTestCase):

    @create_and_login_user()
    def test_get_request_returns_list_of_records_types(self):
        RecordType.create(
            db.session, name="TEST1", ftype=create_ftype("ics"),
            timeframe=RecordType.PIT
        )
        RecordType.create(
            db.session, name="TEST2", ftype=create_ftype("bls"),
            timeframe=RecordType.PIT
        )
        db.session.commit()
        response = self.client.get(url_for("rapi.rtype_list"))
        data = response.json["results"]
        self.assertEqual(len(data), 2)

    @create_and_login_user()
    def test_get_request_returns_proper_data(self):
        rtype = RecordType.create(
            db.session, name="TEST1", ftype=create_ftype("ics"),
            timeframe=RecordType.PIT
        )
        db.session.commit()
        response = self.client.get(url_for("rapi.rtype_list"))
        data = response.json["results"][0]
        self.assertEqual(data["name"], rtype.name)
        self.assertEqual(data["ftype_id"], rtype.ftype.id)

    @create_and_login_user()
    def test_get_request_returns_hyperlinks_to_detail_view(self):
        rtype = RecordType.create(
            db.session, name="TEST1", ftype=create_ftype("ics"),
            timeframe=RecordType.PIT
        )
        RecordTypeRepr.create(db.session, value="TEST Repr", lang="PL", 
                              rtype=rtype)
        db.session.commit()
        response = self.client.get(url_for("rapi.rtype_list"))
        data = response.json["results"][0]
        self.assertIsNotNone(data["uri"])
        self.assertEqual(data["uri"], url_for("rapi.rtype_detail", id=rtype.id))

    @create_and_login_user(role_name="User")
    def test_post_request_creates_dbrequest(self):
        response = self.client.post(
            url_for("rapi.rtype_list"),
            data = json.dumps(
                {"name": "TEST", "statement": "bls"},
                cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        self.assertEqual(db.session.query(DBRequest).count(), 1)

    @create_and_login_user(pass_user=True, role_name="User")
    def test_post_request_creates_dbrequest_with_proper_data(self, user):
        self.client.post(
            url_for("rapi.rtype_list"),
            data = json.dumps(
                {"name": "TEST", "statement": "bls"},
                cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).first()
        data = json.loads(dbrequest.data)
        self.assertEqual(data["name"], "TEST")
        self.assertEqual(data["statement"], "bls") 
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "create")
        self.assertEqual(dbrequest.model, "RecordType")

    # @create_and_login_user()
    # def test_post_request_returns_400_and_error_when_no_name(self):
    #     response = self.client.post(
    #         api.url_for(RecordTypeList),
    #         data = json.dumps(
    #             {"wow": "TEST", "statement": "bls"},
    #             cls=DatetimeEncoder
    #         ),
    #         content_type="application/json"
    #     )
    #     data = response.json["errors"]
    #     self.assertEqual(response.status_code, 400)
    #     self.assertIn("name", data)

    # @create_and_login_user()
    # def test_post_request_returns_400_and_error_when_no_statement(self):
    #     response = self.client.post(
    #         api.url_for(RecordTypeList),
    #         data = json.dumps(
    #             {"name": "TEST", "stm": "bls"},
    #             cls=DatetimeEncoder
    #         ),
    #         content_type="application/json"
    #     )
    #     data = response.json["errors"]
    #     self.assertEqual(response.status_code, 400)
    #     self.assertIn("statement", data)


class TestRecordTypeAPI(AppTestCase):

    @create_and_login_user()
    def test_get_request_returns_recordtype_data(self):
        rtype = RecordType.create(
            db.session, name="TEST1", ftype=create_ftype("ics"),
            timeframe=RecordType.PIT
        )
        db.session.commit()
        response = self.client.get(url_for("rapi.rtype_detail", id=rtype.id))
        data = response.json
        self.assertEqual(data["name"], rtype.name)
        self.assertEqual(data["ftype"], rtype.ftype.name)

    @create_and_login_user()
    def test_get_request_returns_404_when_rtype_does_not_exist(self):
        response = self.client.get(url_for("rapi.rtype_detail", id=1))       
        self.assertEqual(response.status_code, 404)

    @create_and_login_user(pass_user=True)
    def test_delete_request_creates_dbrequest(self, user):
        rtype = RecordType.create(
            db.session, name="TEST1", ftype=create_ftype("ics"),
            timeframe=RecordType.PIT
        )
        db.session.commit() 
        response = self.client.delete(url_for("rapi.rtype_detail", id=rtype.id))
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        dbrequest = db.session.query(DBRequest).first()
        data = json.loads(dbrequest.data)
        self.assertEqual(dbrequest.action, "delete")
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(data["id"], rtype.id)

    @create_and_login_user(pass_user=True)
    def test_put_request_creates_dbrequest(self, user):
        rtype = RecordType.create(
            db.session, name="TEST1", ftype=create_ftype("bls"),
            timeframe=RecordType.PIT
        )
        db.session.commit()
        response = self.client.put(
            url_for("rapi.rtype_detail", id=rtype.id), 
            data=json.dumps({"statement": "bls"}, cls=DatetimeEncoder),
            content_type="application/json"
        )
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        dbrequest = db.session.query(DBRequest).first()
        data = json.loads(dbrequest.data)
        self.assertEqual(dbrequest.action, "update")
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(data["id"], rtype.id)
        self.assertEqual(data["statement"], "bls")