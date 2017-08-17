import unittest
import unittest.mock as mock
import os
from io import BytesIO
import json
from urllib.parse import urlparse
from datetime import datetime, date

from flask import url_for, current_app

from app import db
from app.models import File, User, DBRequest
from app.dbmd.tools import forms
from db import models
from app.rapi.util import DatetimeEncoder

from tests.app import AppTestCase, create_and_login_user


def create_fake_company(isin="#TEST", name="TEST"):
    company = db.session.query(models.Company).filter_by(isin=isin).first()
    if company:
        return company

    company = models.Company(isin="#TEST", name="TEST")
    db.session.add(company)
    db.session.commit()
    return company


def create_ftype(name="ics"):
    ftype = models.FinancialStatementType(name=name)
    db.session.add(ftype)
    db.session.commit()
    return ftype


class MinerIndexViewTest(AppTestCase):

    def send_get_request(self, **kwargs):
        response = self.client.get(
            url_for("dbmd_tools.miner_index"),
            **kwargs
        )    
        return response

    @create_and_login_user()    
    def test_get_request_renders_template(self):
        response = self.send_get_request()
        self.assert_template_used("admin/tools/miner_index.html")
        
    def test_unauthenticated_users_are_redirected(self):
        response = self.send_get_request(follow_redirects = False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlparse(response.location).path, 
            url_for("user.login")
        )
        
    @create_and_login_user(role_name="Visitor")
    def test_unauthorized_users_get_403(self):
        response = self.send_get_request(follow_redirects = False)
        self.assertEqual(response.status_code, 403)

    @create_and_login_user()    
    def test_for_passing_pdf_file_form_to_template(self):
        response = self.send_get_request()
        form = self.get_context_variable("pdf_file_form")
        self.assertIsInstance(form, forms.ReportUploaderForm) 

    @create_and_login_user()    
    def test_for_passing_direct_input_form_to_template(self):
        response = self.send_get_request()
        form = self.get_context_variable("direct_input_form")
        self.assertIsInstance(form, forms.DirectInputForm) 


class PDFFileMinerViewTest(AppTestCase):

    def test_unauthenticated_users_are_redirected(self):
        response = self.client.post(
            url_for("dbmd_tools.pdf_file_miner"),
            follow_redirects = False
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlparse(response.location).path, 
            url_for("user.login")
        )
        
    @create_and_login_user(role_name="Visitor")
    def test_unauthorized_users_get_403(self):
        response = self.client.post(
            url_for("dbmd_tools.pdf_file_miner"),
            follow_redirects = False    
        )
        self.assertEqual(response.status_code, 403)

    @create_and_login_user()    
    def test_render_miner_index_template_when_errors_in_form(self):
        response = self.client.post(
            url_for("dbmd_tools.pdf_file_miner"), follow_redirects=True,
            content_type="multipart/form-data"
        )
        self.assert_template_used("admin/tools/miner_index.html")

    @create_and_login_user()
    def test_for_showing_alert_when_no_file(self):
        response = self.client.post(
            url_for("dbmd_tools.pdf_file_miner"), follow_redirects=True,
            content_type="multipart/form-data"
        )
        content = response.data.decode("utf-8")
        self.assertIn("No file selected", content)

    @create_and_login_user()
    def test_for_showing_alert_when_file_without_name(self):
        data = dict(
            file=(BytesIO(b"Content of the file."), ""),
        )
        response = self.client.post(
            url_for("dbmd_tools.pdf_file_miner"), data=data, 
            follow_redirects=False, content_type="multipart/form-data"
        )
        content = response.data.decode("utf-8")
        self.assertIn("No file selected", content)

    @create_and_login_user()
    def test_for_showing_alert_when_file_with_not_allowed_extension(self):
        data = dict(
            file=(BytesIO(b"Content of the file."), "report.exe"),
        )
        response = self.client.post(
            url_for("dbmd_tools.pdf_file_miner"), data=data, 
            follow_redirects=False, content_type="multipart/form-data"
        )
        content = response.data.decode("utf-8")
        self.assertIn("Not allowed extension", content)

    @create_and_login_user()    
    @mock.patch("app.dbmd.tools.views.render_pdf_file_miner") 
    def test_render_pdf_file_miner_when_form_validates(self, render_mock):
        render_mock.return_value = ""
        data = dict(
            file=(BytesIO(b"Content of the file."), "report.pdf"),
        )
        response = self.client.post(
            url_for("dbmd_tools.pdf_file_miner"), data=data, 
            follow_redirects=False, content_type="multipart/form-data"
        )
        self.assertTrue(render_mock.called)
        

    @unittest.skip #TODO: problem with current_user during tests
    @create_and_login_user(pass_user=True)
    def test_for_creating_entry_in_database(self, user):
        data = dict(
            file=(BytesIO(b"Content of the file."), "report.pdf"),
        )
        response = self.client.post(
            url_for("dbmd_tools.pdf_file_miner"), data=data, 
            follow_redirects=False, content_type="multipart/form-data"
        )
        self.assertEqual(db.session.query(File).count(), 1)
        file = db.session.query(File).first()
        self.assertEqual(file.name, "report.pdf")
        self.assertEqual(file.user, user)


class DirectInputMinerViewTest(AppTestCase):

    def test_unauthenticated_users_are_redirected(self):
        response = self.client.post(
            url_for("dbmd_tools.direct_input_miner"),
            follow_redirects = False
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlparse(response.location).path, 
            url_for("user.login")
        )
        
    @create_and_login_user(role_name="Visitor")
    def test_unauthorized_users_get_403(self):
        response = self.client.post(
            url_for("dbmd_tools.direct_input_miner"),
            follow_redirects = False    
        )
        self.assertEqual(response.status_code, 403)


    @create_and_login_user()    
    def test_render_miner_index_template_when_errors_in_form(self):
        response = self.client.post(
            url_for("dbmd_tools.direct_input_miner"), follow_redirects=True,
            content_type="multipart/form-data"
        )
        self.assert_template_used("admin/tools/miner_index.html")

    @create_and_login_user()
    def test_for_showing_alert_when_no_content(self):
        response = self.client.post(
            url_for("dbmd_tools.direct_input_miner"), follow_redirects=True,
            content_type="multipart/form-data"
        )
        content = response.data.decode("utf-8")
        self.assertIn("This field is required.", content)

    @create_and_login_user()    
    @mock.patch("app.dbmd.tools.views.render_direct_input_miner") 
    def test_render_direct_input_miner_when_form_validates(self, render_mock):
        render_mock.return_value = ""
        company = create_fake_company()
        data = dict(
            content="NET PROFIT      100          200",
            company=str(company.id)
        )
        response = self.client.post(
            url_for("dbmd_tools.direct_input_miner"), data=data, 
            follow_redirects=False, content_type="multipart/form-data"
        )
        self.assertTrue(render_mock.called)


class ParserPostViewTest(AppTestCase):

    def create_fake_report(self, timestamp, timerange, company):
        report = models.Report(
            timestamp=timestamp, timerange=timerange, company=company
        )
        db.session.add(report)
        db.session.commit()
        return report

    def create_data_for_request(self, records=True):
        rtype = models.RecordType(name="NETPROFIT", ftype=create_ftype())
        db.session.add(rtype)
        company = create_fake_company()
        
        data = {
            "timestamp": "2015-03-31", "timerange": 12,
            "company_id": company.id
        }
        if records:
            data["records"] = [
                    {
                        "value": 100, "timerange": 12, "timestamp": "2015-03-31", 
                        "rtype_id": rtype.id, "company_id": company.id
                    },
                    {
                        "value": 150, "timerange": 12, "timestamp": "2014-03-31",
                        "rtype_id": rtype.id, "company_id": company.id
                    }
                ]
                
        return data

    def send_post_request(self, data, **kwargs):
        return self.client.post(
            url_for("dbmd_tools.upload_data"),
            data = {"data": json.dumps(data, cls=DatetimeEncoder) },
            **kwargs
        )

    def test_unauthenticated_users_are_redirected(self):
        response = self.send_post_request({}, follow_redirects=False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlparse(response.location).path, 
            url_for("user.login")
        )
        
    @create_and_login_user(role_name="Visitor")
    def test_unauthorized_users_get_403(self):
        response = self.send_post_request({}, follow_redirects=False)

        self.assertEqual(response.status_code, 403)

    @create_and_login_user()
    def test_create_request_creates_report(self):
        data = self.create_data_for_request(records=False)
        response = self.send_post_request(data)

        self.assertEqual(db.session.query(DBRequest).count(), 1)

        dbrequest = db.session.query(DBRequest).one()
        self.assertEqual(dbrequest.action, "create")
        self.assertEqual(dbrequest.model, "Report")

        data = json.loads(dbrequest.data)
        self.assertEqual(data["timerange"], 12)
        self.assertEqual(data["timestamp"], "2015-03-31")

    @create_and_login_user()
    def test_create_update_request_when_report_exists(self):
        data = self.create_data_for_request(records=False)
        company = create_fake_company()
        report = self.create_fake_report(
            timestamp=datetime.strptime(data["timestamp"], "%Y-%m-%d"),
            timerange=data["timerange"],
            company=company
        )

        response = self.send_post_request(data)

        self.assertEqual(db.session.query(DBRequest).count(), 1)

        dbrequest = db.session.query(DBRequest).one()
        self.assertEqual(dbrequest.action, "update")

        data = json.loads(dbrequest.data)
        self.assertEqual(data["id"], report.id)
        self.assertNotIn("timestamp", data)
        self.assertNotIn("timerange", data)     

    @create_and_login_user()
    def test_lack_of_timestamp_or_timerange_does_not_raise_errors(self):
        data = self.create_data_for_request()
        del data["timerange"]
        del data["timestamp"]

        response = self.send_post_request(data)

    @create_and_login_user()
    def test_empty_string_for_timestamp_and_timerange_are_ok(self):
        data = self.create_data_for_request()
        data["timerange"] = ""
        data["timestamp"] = ""

        response = self.send_post_request(data)

    @create_and_login_user()
    def test_create_subrequests(self):
        data = self.create_data_for_request()

        response = self.send_post_request(data)

        self.assertEqual(db.session.query(DBRequest).count(), 3)

    @create_and_login_user()
    def test_redirect_to_dbmd_index(self):
        data = self.create_data_for_request()
        response = self.send_post_request(data, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlparse(response.location).path, 
            url_for("admin.index")
        )

    @create_and_login_user()
    def test_report_timerange_and_timestamp_are_not_required(self):
        data = self.create_data_for_request(records=False)
        data["timerange"] = ""
        data["timestamp"] = ""

        response = self.send_post_request(data)

        self.assertEqual(db.session.query(DBRequest).count(), 1)
        
        dbrequest = db.session.query(DBRequest).one()
        self.assertIsNone(dbrequest.model)
        self.assertTrue(dbrequest.wrapping_request)

    @create_and_login_user()
    def test_report_timerange_and_timestamp_contains_corrupted_data(self):
        data = self.create_data_for_request(records=False)
        data["timerange"] = "(not identified)"
        data["timestamp"] = "-"

        response = self.send_post_request(data)

        self.assertEqual(db.session.query(DBRequest).count(), 1)
        
        dbrequest = db.session.query(DBRequest).one()
        self.assertIsNone(dbrequest.model)
        self.assertTrue(dbrequest.wrapping_request)


class BatchIndexViewTest(AppTestCase):

    def send_get_request(self, **kwargs):
        response = self.client.get(
            url_for("dbmd_tools.batch_index"),
            **kwargs
        )    
        return response

    @create_and_login_user()    
    def test_get_request_renders_template(self):
        response = self.send_get_request()
        self.assert_template_used("admin/tools/batch_index.html")
        
    def test_unauthenticated_users_are_redirected(self):
        response = self.send_get_request(follow_redirects = False)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlparse(response.location).path, 
            url_for("user.login")
        )
        
    @create_and_login_user(role_name="Visitor")
    def test_unauthorized_users_get_403(self):
        response = self.send_get_request(follow_redirects = False)
        self.assertEqual(response.status_code, 403)

    @create_and_login_user()
    def test_for_passing_batch_uploader_form_to_template(self):
        response = self.send_get_request()
        form = self.get_context_variable("form")
        self.assertIsInstance(form, forms.BatchUploaderForm) 