from datetime import datetime
import json

from flask import url_for

from app import db
from app.rapi import api
from db.serializers import DatetimeEncoder
import db.models as models
from db.models import Company
from app.models import Permission, Role, User, DBRequest

from tests.app import AppTestCase, create_and_login_user


class TestCompanyList(AppTestCase):

    @create_and_login_user()
    def test_get_request_returns_json_response(self):
        response = self.client.get(url_for("rapi.company_list"))
        self.assertEqual(response.content_type, "application/json")

    @create_and_login_user()
    def test_get_request_returns_list_of_companies(self):
        comp1 = Company.create(db.session, name="TEST1", isin="#TEST1")
        comp2 = Company.create(db.session, name="TEST2", isin="#TEST2")
        db.session.commit()
        response = self.client.get(url_for("rapi.company_list"))
        data = response.json["results"]
        self.assertEqual(len(data), 2)

    @create_and_login_user()
    def test_get_request_returns_companies_data(self):
        comp = Company.create(db.session, name="TEST", isin="123#TEST")
        db.session.commit()
        response = self.client.get(url_for("rapi.company_list"))
        data = response.json["results"][0]
        self.assertEqual(data["name"], comp.name)
        self.assertEqual(data["isin"], comp.isin)

    @create_and_login_user()
    def test_get_request_returns_hyperlinks_to_detail_view(self):
        comp = Company.create(db.session, name="TEST", isin="123#TEST")
        models.CompanyRepr.create(db.session, value="TEST Repr", company=comp)
        db.session.commit()
        response = self.client.get(url_for("rapi.company_list"))
        data = response.json["results"][0]
        self.assertIsNotNone(data["uri"])
        self.assertEqual(data["uri"], url_for("rapi.company_detail", id=comp.id))

    # @create_and_login_user()
    # def test_order_results_with_sort_parameter(self):
    #     Company.create(db.session, name="BB", isin="BB")
    #     Company.create(db.session, name="AA", isin="AA")
    #     Company.create(db.session, name="CC", isin="CC")
    #     db.session.commit()
    #     response = self.client.get(
    #         url_for("rapi.company_list"),
    #         query_string={"sort": "name"}
    #     )
    #     data = response.json["results"]
    #     self.assertEqual(data[0]["name"], "AA")
    #     self.assertEqual(data[1]["name"], "BB")
    #     self.assertEqual(data[2]["name"], "CC")

    # @create_and_login_user()
    # def test_sort_in_reverse_order(self):
    #     Company.create(db.session, name="BB", isin="BB")
    #     Company.create(db.session, name="AA", isin="AA")
    #     Company.create(db.session, name="CC", isin="CC")
    #     db.session.commit()
    #     response = self.client.get(
    #         url_for("rapi.company_list"),
    #         query_string={"sort": "-name"}
    #     )
    #     data = response.json["results"]
    #     self.assertEqual(data[0]["name"], "CC")
    #     self.assertEqual(data[1]["name"], "BB")
    #     self.assertEqual(data[2]["name"], "AA")

    # @create_and_login_user()
    # def test_sort_by_two_columns(self):
    #     Company.create(db.session, name="AA", isin="AA", ticker="AA")
    #     Company.create(db.session, name="BB", isin="CC", ticker="BB")     
    #     Company.create(db.session, name="BB", isin="BB", ticker="AA")
    #     response = self.client.get(
    #         url_for("rapi.company_list"),
    #         query_string={"sort": "name, ticker"}
    #     )
    #     data = response.json["results"]
    #     self.assertEqual(data[0]["name"], "AA")
    #     self.assertEqual(data[1]["ticker"], "AA")
    #     self.assertEqual(data[2]["ticker"], "BB")

    @create_and_login_user(role_name="User")
    def test_post_request_creates_dbrequest(self):
        response = self.client.post(
            url_for("rapi.company_list"),
            data = json.dumps(
                {"name": "TEST", "isin": "TEST#ONE", "ticker": "TST" },
                cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        self.assertEqual(db.session.query(DBRequest).count(), 1)

    @create_and_login_user(pass_user=True, role_name="User")
    def test_post_request_creates_dbrequest_with_proper_data(self, user):
        response = self.client.post(
            url_for("rapi.company_list"),
            data = json.dumps(
                {"name": "TEST", "isin": "TEST#ONE", "ticker": "TST" },
                cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).first()
        data = json.loads(dbrequest.data)
        self.assertEqual(data["name"], "TEST")
        self.assertEqual(data["isin"], "TEST#ONE") 
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "create")
        self.assertEqual(dbrequest.model, "Company")

    @create_and_login_user(role_name="Visitor")
    def test_post_request_requires_permission_to_modify_data(self):
        response = self.client.post(
            url_for("rapi.company_list"),
            data = json.dumps(
                {"name": "TEST", "isin": "TEST#ONE", "ticker": "TST" },
                cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 401)

    @create_and_login_user(role_name="Visitor")
    def test_user_without_permission_to_modify_data_can_read_data(self):
        response = self.client.get(url_for("rapi.company_list"))
        self.assertEqual(response.status_code, 200)

    # @create_and_login_user()
    # def test_post_request_returns_400_and_error_when_no_name(self):
    #     response = self.client.post(
    #         api.url_for(CompanyList),
    #         data = json.dumps(
    #             {"logo": "TEST", "isin": "TEST#ONE", "ticker": "TST" },
    #             cls=DatetimeEncoder
    #         ),
    #         content_type="application/json"
    #     ) 
    #     data = response.json["errors"]
    #     self.assertEqual(response.status_code, 400)
    #     self.assertIn("name", data)

    # @create_and_login_user()
    # def test_post_request_returns_400_and_error_when_no_isin(self):
    #     response = self.client.post(
    #         api.url_for(CompanyList),
    #         data = json.dumps(
    #             {"name": "TEST", "isi": "TEST#ONE", "ticker": "TST" },
    #             cls=DatetimeEncoder
    #         ),
    #         content_type="application/json"
    #     ) 
    #     data = response.json["errors"]
    #     self.assertEqual(response.status_code, 400)
    #     self.assertIn("isin", data)

    # @create_and_login_user()
    # def test_post_request_returns_400_when_not_unique_isin(self):
    #     comp = Company.create(db.session, name="TEST", isin="123#TEST")
    #     db.session.commit()
    #     response = self.client.post(
    #         api.url_for(CompanyList),
    #         data = json.dumps(
    #             {"name": "TEST", "isin": "123#TEST", "ticker": "TST" },
    #             cls=DatetimeEncoder
    #         ),
    #         content_type="application/json"
    #     ) 
    #     data = response.json["errors"]
    #     self.assertEqual(response.status_code, 400)
    #     self.assertIn("isin", data)
