from datetime import datetime
import json

from flask import url_for

from app import db
from app.rapi import api
from db.serializers import DatetimeEncoder
import db.models as models
from db.models import Company, RecordType, Record, FinancialStatement
from app.models import Permission, Role, User, DBRequest

from tests.app import AppTestCase, create_and_login_user



def generate_data(name="TEST", timeframe=RecordType.POT):
    company = Company.create(db.session, name=name, isin="#"+name)
    ftype = FinancialStatement.get_or_create(db.session, name="bls")
    rtype = RecordType.get_or_create(
        db.session, {"ftype": ftype, "timeframe": timeframe}, 
        name="NET_PROFIT"
    )
    rec1 = Record.create(
        db.session, value=10, timerange=3, timestamp=datetime(2015, 3, 31),
        rtype=rtype, company=company
    )
    rec2 = Record.create(
        db.session, value=20, timerange=3, timestamp=datetime(2014, 3, 31),
        rtype=rtype, company=company
    )
    db.session.commit()      
    return {
        "company": company,
        "rtype": rtype,
        "records": [ rec1, rec2 ]
    }


class TestListView(AppTestCase):

    @create_and_login_user()
    def test_get_request_returns_list_of_records(self):
        data = generate_data()
        generate_data(name="FAKE_TEST")
        response = self.client.get(
            url_for("rapi.company_record_list", id=data["company"].id)
        )
        data = response.json
        self.assertEqual(data["count"], 2)

    @create_and_login_user()
    def test_get_request_raise_404_when_no_company(self):
        response = self.client.get(url_for("rapi.company_record_list", id=1))
        self.assertEqual(response.status_code, 404)

    @create_and_login_user(pass_user=True, role_name="User")
    def test_post_request_creates_dbrequest(self, user):
        test_data = generate_data()
        response = self.client.post(
            url_for("rapi.company_record_list", id=test_data["company"].id),
            data=json.dumps({
                "value": 10, "timerange": 3,
                "timestamp": datetime(2017, 3, 31), "rtype": test_data["rtype"].id
            }, cls=DatetimeEncoder),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).one()
        self.assertIsNotNone(dbrequest)
        data = json.loads(dbrequest.data)
        self.assertEqual(data["value"], 10)
        self.assertEqual(data["rtype"], test_data["rtype"].id) 
        self.assertEqual(data["company_id"], test_data["company"].id)
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "create")
        self.assertEqual(dbrequest.model, "Record")

    @create_and_login_user()
    def test_post_request_uses_company_id_from_url(self):
        test_data = generate_data()
        response = self.client.post(
            url_for("rapi.company_record_list", id=test_data["company"].id),
            data=json.dumps({
                "value": 10, "timerange": 3, "timestamp": datetime(2017, 3, 31), 
                "rtype": test_data["rtype"].id, "company": 1234
            }, cls=DatetimeEncoder),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).one()
        data = json.loads(dbrequest.data)
        self.assertEqual(data["company_id"], test_data["company"].id)


class TestDetailView(AppTestCase):

    @create_and_login_user()
    def test_get_request_returns_record_data(self):
        test_data = generate_data()        
        response = self.client.get(
            url_for("rapi.company_record_detail", id=test_data["company"].id, 
                    rid=test_data["records"][0].id)
        )
        data = response.json
        record = test_data["records"][0]
        self.assertEqual(data["value"], record.value)
        self.assertEqual(data["timerange"], record.timerange)

    @create_and_login_user(pass_user=True)
    def test_put_request_creates_dbrequet(self, user):
        test_data = generate_data()        
        self.client.put(
            url_for("rapi.company_record_detail", id=test_data["company"].id, 
                    rid=test_data["records"][0].id),
            data=json.dumps(
                {"value": 15, "timerange": 12},
                cls=DatetimeEncoder
            ),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        data = json.loads(dbrequest.data)
        self.assertEqual(dbrequest.action, "update")
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(data["timerange"], 12)
        self.assertEqual(data["value"], 15)

    @create_and_login_user(pass_user=True)
    def test_delete_request_creates_dbrequest(self, user):
        test_data = generate_data()   
        self.client.delete(
            url_for("rapi.company_record_detail", id=test_data["company"].id, 
                    rid=test_data["records"][0].id)
        )
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        self.assertEqual(dbrequest.action, "delete")
        self.assertEqual(dbrequest.user, user)

    @create_and_login_user()
    def test_for_raising_404_when_invalid_company_id(self):
        test_data = generate_data()  
        fake_data = generate_data(name="FAKE")
        response = self.client.get(
            url_for("rapi.company_record_detail", id=fake_data["company"].id, 
                    rid=test_data["records"][0].id)
        )
        self.assertEqual(response.status_code, 404)

    @create_and_login_user()
    def test_for_raising_404_when_invalid_record_id(self):
        test_data = generate_data()  
        fake_data = generate_data(name="FAKE")
        response = self.client.get(
            url_for("rapi.company_record_detail", id=test_data["company"].id, 
                    rid=fake_data["records"][0].id)
        )
        self.assertEqual(response.status_code, 404)