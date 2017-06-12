from io import BytesIO
import os
from unittest.mock import patch, Mock
import json

from flask import url_for, current_app

from tests.app import AppTestCase

from db.models import Company, ItemType, ItemTypeRepr
from app.models import File
from app import db


@patch("app.reports.views.FinancialReport")
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

	def test_for_creating_financial_document(self, report_mock):
		report_mock.return_value.company = dict()
		report_mock.return_value.rows = list()
		file = self.create_fake_file()

		response = self.client.get(
			url_for("reports.parser"), data={"file_id": file.id}
		)

		self.assertTrue(report_mock.called_once)

	def test_initialize_financial_document_with_proper_file(
		self, report_mock
	):
		report_mock.return_value.company = dict()
		report_mock.return_value.rows = list()
		file = self.create_fake_file()

		response = self.client.get(
			url_for("reports.parser"), data={"file_id": file.id}
		)

		filepath = report_mock.call_args[0][0]
		self.assertEqual(
			filepath,
			os.path.join(current_app.config.get("UPLOAD_FOLDER"), file.name)
		)

	def test_for_raising_404_when_file_id_does_not_exist(self, report_mock):
		report_mock.return_value.company = dict()
		report_mock.return_value.rows = list()
		response = self.client.get(
			url_for("reports.parser"), data={"file_id": 1}
		)
		self.assertEqual(response.status_code, 404)

	def test_for_raising_400_when_no_file_id(self, report_mock):
		report_mock.return_value.company = dict()
		report_mock.return_value.rows = list()
		file = self.create_fake_file()
		response = self.client.get(url_for("reports.parser"))
		self.assertEqual(response.status_code, 400)

	def test_for_rendering_proper_template(self, report_mock):
		report_mock.return_value.company = dict()
		report_mock.return_value.rows = list()
		file = self.create_fake_file()
		response = self.client.get(
			url_for("reports.parser"), data={"file_id": file.id}
		)
		self.assert_template_used("reports/parser.html")

	def test_for_passing_report_to_template(self, report_mock):
		temp_mock = Mock()
		temp_mock.company = dict(name="TEST")
		temp_mock.rows = list()
		report_mock.return_value = temp_mock
		file = self.create_fake_file()
		response = self.client.get(
			url_for("reports.parser"), data={"file_id": file.id}
		)
		report = self.get_context_variable("report")
		self.assertEqual(id(report), id(temp_mock))

	def test_for_passing_list_of_field_types_to_template(self, report_mock):
		temp_mock = Mock()
		temp_mock.rows = list()
		temp_mock.company = dict()
		report_mock.return_value = temp_mock
		file = self.create_fake_file()

		# create some fields for testing
		ItemType.create(db.session, name="FIXED_ASSETS")
		ItemType.create(db.session, name="LIABILITIES")
		db.session.commit()

		response = self.client.get(
			url_for("reports.parser"), data={"file_id": file.id}
		)		
		fields = self.get_context_variable("fields")

		self.assertEqual(len(fields), 2)
		self.assertIn("FIXED_ASSETS", fields)
		self.assertIn("LIABILITIES", fields)

	def test_for_raising_500_when_there_is_no_file_in_the_disc(self, rmock):
		rmock.return_value.company = dict()
		rmock.return_value.rows = list()
		file = self.create_fake_file()
		os.remove(os.path.join(current_app.config.get("UPLOAD_FOLDER"), 
			                   file.name))
		response = self.client.get(
			url_for("reports.parser"), data={"file_id": file.id}
		)
		self.assertEqual(response.status_code, 500)

	def test_for_passing_company_to_template(self, rmock):
		file = self.create_fake_file()
		company = self.create_fake_company()
		fr = Mock()
		fr.company = { "isin": company.isin }
		fr.rows = list()
		rmock.return_value = fr

		response = self.client.get(
			url_for("reports.parser"), data={"file_id": file.id}
		)

		ctx_company = self.get_context_variable("company")
		self.assertEqual(ctx_company, company)


@patch("app.reports.views.dbutil")
@patch("app.reports.views.putil.identify_records_in_text")
class TextParserViewTest(AppTestCase):

	# override setUp and tearDown methods of parent class to prevent from
	# creating db what takes a while
	def setUp(self):
		pass
	def tearDown(self):
		pass

	def test_for_raising_400_when_no_text(self, pmock, dbmock):
		response = self.client.post(url_for("reports.textparser"))
		self.assertEqual(response.status_code, 400)

	def test_for_calling_identify_records_in_text(self, pmock, dbmock):
		response = self.client.post(
			url_for("reports.textparser"), 
			data={"text": b"NET PROFIT  10  20", "spec": "bls"}
		)
		self.assertTrue(pmock.called)

	def test_for_raising_400_when_invalid_specificiation(self, pmock, dbmock):
		response = self.client.post(
			url_for("reports.textparser"), 
			data={"text": b"NET PROFIT  10  20", "spec": "no_spec"}
		)
		self.assertEqual(response.status_code, 400)

	def test_for_calling_get_finrecords_reprs_with_proper_statement(
		self, pmock, dbmock
	):
		func_mock = Mock()
		dbmock.get_finrecords_reprs = func_mock
		response = self.client.post(
			url_for("reports.textparser"), 
			data={"text": b"NET PROFIT  10  20", "spec": "bls"}
		)
		self.assertEqual(func_mock.call_args[0][1].upper(), "BLS")

	def test_response_contains_idetified_records(self, pmock, dbmock):
		pmock.return_value = [
			(("TEST_NAME", 0.99), [5, 10, 15], (0,)),
			(("NEXT_NAME", 0.80), [100, 150], (1,))
		]
		response = self.client.post(
			url_for("reports.textparser"), 
			data={"text": b"NET PROFIT  10  20", "spec": "bls"}
		)
		records = json.loads(response.data.decode("utf-8"))
		self.assertEqual(len(records), 2)
		record = next(filter(lambda x: x["name"] == "TEST_NAME", records))
		self.assertEqual(record["numbers"], [5, 10, 15])


class TestLoadReportView(AppTestCase):

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

	def test_get_request_renders_template(self):
		response = self.client.get(url_for("reports.load_report"))
		self.assert_template_used("reports/loader.html")

	def test_for_creating_entry_in_database(self):
		data = dict(
			file=(BytesIO(b"Content of the file."), "report.pdf"),
		)
		response = self.client.post(
			url_for("reports.load_report"), data=data, follow_redirects=True,
			content_type="multipart/form-data"
		)
		self.assertEqual(db.session.query(File).count(), 1)
		file = db.session.query(File).first()
		self.assertEqual(file.name, "report.pdf")

	def test_for_saving_file_to_disc(self):
		data = dict(
			file=(BytesIO(b"Content of the file."), "report.pdf"),
		)
		response = self.client.post(
			url_for("reports.load_report"), data=data, follow_redirects=True,
			content_type="multipart/form-data"
		)
		self.assertTrue(os.path.exists(
			os.path.join(self.app.config["UPLOAD_FOLDER"], data["file"][1])
		))

	def test_for_showing_alert_when_no_file(self):
		response = self.client.post(
			url_for("reports.load_report"), follow_redirects=True,
			content_type="multipart/form-data"
		)
		content = response.data.decode("utf-8")
		self.assertIn("No selected file", content)

	def test_for_showing_alert_when_file_without_name(self):
		data = dict(
			file=(BytesIO(b"Content of the file."), ""),
		)
		response = self.client.post(
			url_for("reports.load_report"), data=data, follow_redirects=True,
			content_type="multipart/form-data"
		)
		content = response.data.decode("utf-8")
		self.assertIn("No selected file", content)

	def test_for_showing_alert_when_file_with_not_allowed_extension(self):
		data = dict(
			file=(BytesIO(b"Content of the file."), "report.exe"),
		)
		response = self.client.post(
			url_for("reports.load_report"), data=data, follow_redirects=True,
			content_type="multipart/form-data"
		)
		content = response.data.decode("utf-8")
		self.assertIn("Not allowed extension", content)

	def test_for_redirecting_after_successful_read(self):
		data = dict(
			file=(BytesIO(b"Content of the file."), "report.txt"),
		)
		response = self.client.post(
			url_for("reports.load_report"), data=data, follow_redirects=False,
			content_type="multipart/form-data"
		)
		self.assertRedirects(response, url_for("reports.parser"))

	@patch("app.reports.views.requests.get")
	def test_for_downloading_file_from_external_webpage_when_url(
		self, rget_mock
	):
		data = dict(url="http://localhost:5000/test.txt")
		response = self.client.post(
			url_for("reports.load_report"), data=data, follow_redirects=True,
			content_type="multipart/form-data"
		)
		self.assertTrue(rget_mock.called)

	@patch("app.reports.views.requests.get")
	def test_for_showing_alert_when_invalid_url(self, rget_mock):
		rmock = Mock()
		rmock.status_code = 404
		rget_mock.return_value = rmock
		data = dict(url="http://localhost:5000/test.txt")
		response = self.client.post(
			url_for("reports.load_report"), data=data, follow_redirects=True,
			content_type="multipart/form-data"
		)	
		content = response.data.decode("utf-8")
		self.assertIn("Unable to load file from given url", content)

	@patch("app.reports.views.requests.get")
	def test_for_saving_file_from_external_webpage(self, rget_mock):
		rmock = Mock()
		rmock.status_code = 200
		temp = Mock()
		temp.return_value = iter([b"Test", b"report"])
		setattr(rmock, "__iter__", temp)
		rget_mock.return_value = rmock

		data = dict(url="http://localhost:5000/test.txt")
		response = self.client.post(
			url_for("reports.load_report"), data=data, follow_redirects=True,
			content_type="multipart/form-data"
		)	
		self.assertTrue(os.path.exists(
			os.path.join(self.app.config["UPLOAD_FOLDER"], 
				         data["url"].split("/")[-1])
		))


class TestFieldsView(AppTestCase):

	def setUp(self):
		ItemTypeRepr.__table__.create(db.session.bind)
		ItemType.__table__.create(db.session.bind)

	def tearDown(self):
		ItemTypeRepr.__table__.drop(db.session.bind)
		ItemType.__table__.drop(db.session.bind)
		db.session.remove()

	def test_for_retrieving_types_of_items_with_get_request(self):
		rtype1 = ItemType.create(db.session, name="FIXED_ASSETS")
		rtype2 = ItemType.create(db.session, name="LIABILITIES")
		db.session.commit()
		response = self.client.get(url_for("reports.fields"))
		data = response.json
		self.assertEqual(len(data), 2)