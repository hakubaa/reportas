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
from app.dbmd.tools.forms import ReportUploaderForm
from db import models
from db.models import Company
from app.rapi.util import DatetimeEncoder

from tests.app import AppTestCase, create_and_login_user


class LoaderViewTest(AppTestCase):

    def tearDown(self):
        super().tearDown()
        # remove all files from uploads_test
        folder = self.app.config.get("UPLOAD_FOLDER")
        for file in os.listdir(folder):
            file_path = os.path.join(folder, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                pass
            
    @create_and_login_user()    
    def test_get_request_renders_template(self):
        response = self.client.get(url_for("dbmd_tools.report_uploader"))
        self.assert_template_used("admin/tools/report_uploader.html")
        
    def test_unauthenticated_users_are_redirected(self):
        response = self.client.get(
            url_for("dbmd_tools.report_uploader"),
            follow_redirects = False
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlparse(response.location).path, 
            url_for("user.login")
        )
        
    @create_and_login_user(role_name="Visitor")
    def test_unauthorized_users_get_403(self):
        response = self.client.get(
            url_for("dbmd_tools.report_uploader"),
            follow_redirects = False    
        )
        self.assertEqual(response.status_code, 403)
    
    @create_and_login_user()    
    def test_for_passing_proper_form_to_template(self):
        response = self.client.get(url_for("dbmd_tools.report_uploader"))
        form = self.get_context_variable("form")
        self.assertIsInstance(form, ReportUploaderForm)
    
    @create_and_login_user()    
    def test_for_saving_file_to_disc(self):
        data = dict(
            file=(BytesIO(b"Content of the file."), "report.pdf"),
        )
        response = self.client.post(
            url_for("dbmd_tools.report_uploader"), data=data, 
            follow_redirects=False, content_type="multipart/form-data"
        )
        self.assertTrue(os.path.exists(
            os.path.join(self.app.config["UPLOAD_FOLDER"], data["file"][1])
        ))
        
    @create_and_login_user()    
    def test_for_redirecting_after_successful_read(self):
        data = dict(
            file=(BytesIO(b"Content of the file."), "report.pdf"),
        )
        response = self.client.post(
            url_for("dbmd_tools.report_uploader"), data=data, 
            follow_redirects=False, content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlparse(response.location).path, 
            url_for("dbmd_tools.parser")
        )
        
    @create_and_login_user()
    def test_for_showing_alert_when_no_file(self):
        response = self.client.post(
            url_for("dbmd_tools.report_uploader"), follow_redirects=True,
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
            url_for("dbmd_tools.report_uploader"), data=data, 
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
            url_for("dbmd_tools.report_uploader"), data=data, 
            follow_redirects=False, content_type="multipart/form-data"
        )
        content = response.data.decode("utf-8")
        self.assertIn("Not allowed extension", content)

    @unittest.skip #TODO: problem with current_user during tests
    @create_and_login_user(pass_user=True)
    def test_for_creating_entry_in_database(self, user):
        data = dict(
            file=(BytesIO(b"Content of the file."), "report.pdf"),
        )
        response = self.client.post(
            url_for("dbmd_tools.report_uploader"), data=data, 
            follow_redirects=False, content_type="multipart/form-data"
        )
        self.assertEqual(db.session.query(File).count(), 1)
        file = db.session.query(File).first()
        self.assertEqual(file.name, "report.pdf")
        self.assertEqual(file.user, user)


@mock.patch("app.dbmd.tools.views.read_report_from_file")
@mock.patch("app.dbmd.tools.views.get_company")
class ParserViewTest(AppTestCase):

    def create_fake_file(self, name="test.pdf", content=b"test"):
        file = File(name=name)
        db.session.add(file)
        db.session.commit()
        path = os.path.join(current_app.config.get("UPLOAD_FOLDER"), name)
        with open(path, "wb") as f:
            f.write(content)
        return file

    def create_fake_company(self, name="TEST", fullname="TEST COMPANY", 
                            isin="TEST"):
        company = Company(name=name, fullname=fullname, isin=isin)
        db.session.add(company)
        db.session.commit()
        return company
        
    @create_and_login_user()
    def test_render_proper_template(self, company_mock, report_mock):
        file = self.create_fake_file()
        response = self.client.get(
            url_for("dbmd_tools.parser"), query_string = {"filename": file.name}
        )
        self.assert_template_used("admin/tools/parser.html")
        
    @create_and_login_user()
    def test_for_redirecting_to_report_uploader_file_doest_not_exist(
        self, company_mock, report_mock
    ):
        response = self.client.get(
            url_for("dbmd_tools.parser"), 
            query_string = {"filename": "report.pdf"},
            follow_redirects=False
        )
        self.assertRedirects(response, url_for("dbmd_tools.report_uploader"))
     
    @create_and_login_user()
    def test_for_redirecting_to_report_uploader_when_no_filename(
        self, company_mock, report_mock
    ):
        response = self.client.get(
            url_for("dbmd_tools.parser"), follow_redirects=False
        )
        self.assertRedirects(response, url_for("dbmd_tools.report_uploader"))
        
    @create_and_login_user()
    def test_for_creating_financial_report(self, company_mock, report_mock):
        file = self.create_fake_file()
    
        response = self.client.get(
            url_for("dbmd_tools.parser"), query_string = {"filename": file.name}
        )
        
        self.assertTrue(report_mock.called_once)
    
    @create_and_login_user()
    def test_for_passing_report_to_template(self, company_mock, report_mock):
        fake_report = mock.Mock()
        fake_report.company = dict()
        fake_report.rows = []
        fake_report.bls.items.return_value = []
        fake_report.bls.names = []
        fake_report.ics.items.return_value = []
        fake_report.ics.names = []
        fake_report.cfs.items.return_value = []
        fake_report.cfs.names = []
        report_mock.return_value = fake_report
        file = self.create_fake_file()
    
        response = self.client.get(
            url_for("dbmd_tools.parser"), query_string = {"filename": file.name}
        )
        
        report = self.get_context_variable("report")
        self.assertIsNotNone(report)
        self.assertEqual(report, fake_report)

    def test_unauthenticated_users_are_redirected(
        self, company_mock, report_mock
    ):
        response = self.client.get(
            url_for("dbmd_tools.parser"), follow_redirects = False
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlparse(response.location).path, 
            url_for("user.login")
        )
        
    @create_and_login_user(role_name="Visitor")
    def test_unauthorized_users_get_403(self, company_mock, report_mock):
        response = self.client.get(
            url_for("dbmd_tools.parser"), follow_redirects = False    
        )
        self.assertEqual(response.status_code, 403)


class ParserPostViewTest(AppTestCase):

    def create_fake_company(self, isin="#TEST", name="TEST"):
        company = db.session.query(models.Company).filter_by(isin=isin).first()
        if company:
            return company

        company = models.Company(isin="#TEST", name="TEST")
        db.session.add(company)
        db.session.commit()
        return company

    def create_fake_report(self, timestamp, timerange, company):
        report = models.Report(
            timestamp=timestamp, timerange=timerange, company=company
        )
        db.session.add(report)
        db.session.commit()
        return report

    def create_data_for_request(self, records=True):
        rtype = models.RecordType(name="NETPROFIT", statement="nls")
        db.session.add(rtype)
        company = self.create_fake_company()
        
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
            url_for("dbmd_tools.parser_post"),
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
    def test_create_request_to_create_report(self):
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
        company = self.create_fake_company()
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