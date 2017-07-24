import unittest
import unittest.mock as mock
import os
from io import BytesIO
from urllib.parse import urlparse

from flask import url_for, current_app

from app import db
from app.models import File
from app.dbmd.tools.forms import ReportUploaderForm
from db.models import Company

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
        report_mock.return_value = fake_report
        file = self.create_fake_file()
    
        response = self.client.get(
            url_for("dbmd_tools.parser"), query_string = {"filename": file.name}
        )
        
        report = self.get_context_variable("report")
        self.assertIsNotNone(report)
        self.assertEqual(report, fake_report)
      
    @create_and_login_user()  
    def test_for_passing_company_to_template(self, company_mock, report_mock):
        file = self.create_fake_file()
        company = self.create_fake_company()
        fr = mock.Mock()
        fr.company = { "isin": company.isin }
        fr.rows = list()
        report_mock.return_value = fr
        company_mock.return_value = company

        response = self.client.get(
            url_for("dbmd_tools.parser"), query_string = {"filename": file.name}
        )

        ctx_company = self.get_context_variable("company")
        self.assertEqual(ctx_company, company)

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