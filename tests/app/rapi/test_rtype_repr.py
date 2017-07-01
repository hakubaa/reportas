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



class TestListView(AppTestCase):

    def create_rtype_with_reprs(self, n=2, name="TEST"):
        rtype = RecordType.create(db.session, name=name, statement="NLS")
        for i in range(n):
            rtype.reprs.append(
                RecordTypeRepr.create(
                    db.session, 
                    value="Test Repr. #{}".format(i), lang="PL"
                )
            )
        return rtype

    @create_and_login_user()
    def test_for_retrieving_list_of_reprs(self):
        rtype = self.create_rtype_with_reprs(n=2)
        db.session.commit()
        response = self.client.get(url_for("rapi.rtype_repr_list", id=rtype.id))
        data = response.json["results"]
        self.assertEqual(len(data), 2)

    @create_and_login_user()
    def test_get_request_returns_correct_data(self):
        rtype = self.create_rtype_with_reprs(n=1)
        self.create_rtype_with_reprs(n=100, name="FAKE_REPR")
        db.session.commit()
        response = self.client.get(url_for("rapi.rtype_repr_list", id=rtype.id))
        data = response.json["results"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["value"], rtype.reprs[0].value)
        self.assertEqual(data[0]["lang"], rtype.reprs[0].lang)  

    @create_and_login_user()
    def test_get_request_raise_404_when_no_rtype(self):
        rtype = self.create_rtype_with_reprs(n=1)
        db.session.commit()
        response = self.client.get(
            url_for("rapi.rtype_repr_list", id=rtype.id+1)
        )
        self.assertEqual(response.status_code, 404)

    @create_and_login_user(pass_user=True)
    def test_post_request_creates_dbrequest(self, user):
        rtype = self.create_rtype_with_reprs(n=0)
        db.session.commit()
        response = self.client.post(
            url_for("rapi.rtype_repr_list", id=rtype.id),
            data=json.dumps(
                {"lang": "PL", "value": "NEW REPR"}, cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        self.assertEqual(db.session.query(DBRequest).count(), 1)

    @create_and_login_user(pass_user=True)
    def test_post_request_creates_dbrequest_with_proper_data(self, user):
        rtype = self.create_rtype_with_reprs(n=0)
        db.session.commit()
        response = self.client.post(
            url_for("rapi.rtype_repr_list", id=rtype.id),
            data=json.dumps(
                {"lang": "PL", "value": "NEW REPR"}, cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).first()
        data = json.loads(dbrequest.data)
        self.assertEqual(data["lang"], "PL")
        self.assertEqual(data["value"], "NEW REPR") 
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "create")
        self.assertEqual(dbrequest.model, "RecordTypeRepr")

    @create_and_login_user(pass_user=True)
    def test_rtype_is_set_by_default_in_dbrequest(self, user):
        rtype = self.create_rtype_with_reprs(n=0)
        db.session.commit()
        response = self.client.post(
            url_for("rapi.rtype_repr_list", id=rtype.id),
            data=json.dumps(
                {"lang": "PL", "value": "NEW REPR"}, cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).first()
        data = json.loads(dbrequest.data)   
        self.assertEqual(data["rtype"], rtype.id)


    # @create_and_login_user()
    # def test_limit_restuls_with_limit_and_offset(self):
    #     rtype = self.create_rtype_with_reprs(n=10)
    #     db.session.commit()
    #     response = self.client.get(
    #         url_for("rapi.rtype_repr_list", id=rtype.id),
    #         query_string={"limit": 5, "offset": 6}
    #     )
    #     data = response.json
    #     self.assertEqual(data["count"], 4)

    # @create_and_login_user()
    # def test_order_results_with_sort_parameter(self):
    #     rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
    #     rtype.reprs.append(
    #         RecordTypeRepr.create(db.session, value="CC", lang="PL")
    #     )
    #     rtype.reprs.append(
    #         RecordTypeRepr.create(db.session, value="BB", lang="PL")
    #     )
    #     rtype.reprs.append(
    #         RecordTypeRepr.create(db.session, value="AA", lang="PL")
    #     )
    #     db.session.commit()

    #     response = self.client.get(
    #         url_for("rapi.rtype_repr_list", id=rtype.id),
    #         query_string={"sort": "value"}
    #     )

    #     data = response.json["results"]
    #     self.assertEqual(data[0]["value"], "AA")
    #     self.assertEqual(data[1]["value"], "BB")
    #     self.assertEqual(data[2]["value"], "CC")

    # @create_and_login_user()
    # def test_sort_in_reverse_order(self):
    #     rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
    #     rtype.reprs.append(
    #         RecordTypeRepr.create(db.session, value="CC", lang="PL")
    #     )
    #     rtype.reprs.append(
    #         RecordTypeRepr.create(db.session, value="BB", lang="PL")
    #     )
    #     rtype.reprs.append(
    #         RecordTypeRepr.create(db.session, value="AA", lang="PL")
    #     )
    #     db.session.commit()

    #     response = self.client.get(
    #         url_for("rapi.rtype_repr_list", id=rtype.id),
    #         query_string={"sort": "-value"}
    #     )

    #     data = response.json["results"]
    #     self.assertEqual(data[0]["value"], "CC")
    #     self.assertEqual(data[1]["value"], "BB")
    #     self.assertEqual(data[2]["value"], "AA")

    # @create_and_login_user()
    # def test_sort_by_two_columns(self):
    #     rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
    #     rtype.reprs.append(
    #         RecordTypeRepr.create(db.session, value="CC", lang="BB")
    #     )
    #     rtype.reprs.append(
    #         RecordTypeRepr.create(db.session, value="BB", lang="AA")
    #     )
    #     rtype.reprs.append(
    #         RecordTypeRepr.create(db.session, value="AA", lang="BB")
    #     )
    #     db.session.commit()

    #     response = self.client.get(
    #         url_for("rapi.rtype_repr_list", id=rtype.id),
    #         query_string={"sort": "lang, -value"}
    #     )

    #     data = response.json["results"]
    #     self.assertEqual(data[0]["value"], "BB")
    #     self.assertEqual(data[1]["value"], "CC")
    #     self.assertEqual(data[2]["value"], "AA")



class TestDetailView(AppTestCase):

    def create_rtype_with_reprs(self, n=2, name="TEST"):
        rtype = RecordType.create(db.session, name=name, statement="NLS")
        for i in range(n):
            rtype.reprs.append(
                RecordTypeRepr.create(
                    db.session, 
                    value="Test Repr. #{}".format(i), lang="PL"
                )
            )
        return rtype

    @create_and_login_user()
    def test_get_request_returns_repr_of_rtype(self):
        rtype = self.create_rtype_with_reprs(n=1)
        db.session.commit()
        response = self.client.get(
            url_for("rapi.rtype_repr_detail", id=rtype.id, rid=rtype.reprs[0].id)
        )
        data = response.json
        self.assertEqual(data["value"], "Test Repr. #0")
        self.assertEqual(data["lang"], "PL")

    @create_and_login_user(pass_user=True)
    def test_put_request_creates_dbrequet(self, user):
        rtype = self.create_rtype_with_reprs(n=1)
        db.session.commit()
        self.client.put(
            url_for("rapi.rtype_repr_detail", id=rtype.id, rid=rtype.reprs[0].id),
            data=json.dumps(
                {"value": "New Test Repr", "lang": "EN"},
                cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        data = json.loads(dbrequest.data)
        self.assertEqual(dbrequest.action, "update")
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(data["id"], rtype.reprs[0].id)
        self.assertEqual(data["value"], "New Test Repr")

    @create_and_login_user(pass_user=True)
    def test_delete_request_deletes_repr(self, user):
        rtype = self.create_rtype_with_reprs(n=1)
        db.session.commit()
        self.client.delete(
            url_for("rapi.rtype_repr_detail", id=rtype.id, rid=rtype.reprs[0].id),
        )
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        self.assertEqual(dbrequest.action, "delete")
        self.assertEqual(dbrequest.user, user)