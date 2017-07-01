from datetime import datetime
import json

from flask import url_for

from app import db
from app.rapi import api
from app.rapi.util import DatetimeEncoder
from app.rapi.resources import (
    CompanyList, CompanyReprList, RecordTypeList
)
from db.models import (
    Company, Report, CompanyRepr, RecordType, RecordTypeRepr, Record
)
from app.models import Permission, Role, User

from tests.app import AppTestCase, create_and_login_user



class TestRecordList(AppTestCase):

    def create_company_and_rtype(self):
        company = Company.create(db.session, name="TEST", isin="#TEST")
        rtype = RecordType.create(db.session, name="NET_PROFIT", 
                                  statement="NLS")
        db.session.commit()
        return company, rtype

    @create_and_login_user()
    def test_for_creating_one_record_with_post_request(self):
        company, rtype = self.create_company_and_rtype()
        response = self.client.post(
            url_for("rapi.record_list"),
            data=json.dumps({
                "value": 10, "timerange": 3, "rtype": rtype.id,
                "company": company.id, "timestamp": datetime(2015, 3, 31)
            }, cls=DatetimeEncoder),
            content_type="application/json"
        )
        self.assertEqual(db.session.query(Record).count(), 1)
        record = db.session.query(Record).one()
        self.assertEqual(record.company_id, company.id)

    @create_and_login_user()
    def test_for_creating_multiplie_records_with_post_request(self):
        company, rtype = self.create_company_and_rtype()
        response = self.client.post(
            url_for("rapi.record_list"),
            data=json.dumps([
                {
                    "value": 10, "timerange": 3, "rtype": rtype.id,
                    "company": company.id, "timestamp": datetime(2015, 3, 31)
                },
                {
                    "value": 100, "timerange": 3, "rtype": rtype.id,
                    "company": company.id, "timestamp": datetime(2016, 3, 31)
                }
            ], cls=DatetimeEncoder),
            query_string={"many": True},
            content_type="application/json"
        )
        self.assertEqual(db.session.query(Record).count(), 2)

    @create_and_login_user()
    def test_for_returning_only_request_fields(self):
        company, rtype = self.create_company_and_rtype()
        rec1 = Record.create(
            db.session, timerange=3, timestamp=datetime(2016, 3, 31),
            value=10, rtype=rtype, company=company
        )
        rec2 = Record.create(
            db.session, timerange=3, timestamp=datetime(2015, 3, 31),
            value=5, rtype=rtype, company=company
        )
        db.session.commit()
        
        response = self.client.get(
            url_for("rapi.record_list"),
            query_string={"fields": "timerange, value"}
        )
        data = response.json["results"]
        self.assertEqual(set(data[0].keys()), set(("value", "timerange")))
        self.assertEqual(set(data[1].keys()), set(("value", "timerange")))