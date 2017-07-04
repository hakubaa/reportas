import unittest.mock as mock 
from io import BytesIO
import os

from flask import url_for

from tests.app import AppTestCase, create_and_login_user
from db.models import RecordType, RecordTypeRepr
from app import db


class TextParserTest(AppTestCase):
    
    @create_and_login_user()
    def test_400_when_request_did_not_send_text_for_parsing(self):
        response = self.client.post(
            url_for("rapi.parser"),
            query_string={"type": "text"}
        )
        self.assertEqual(response.status_code, 400)

    @create_and_login_user()
    def test_400_when_invalid_specifcation_name(self):
        response = self.client.post(
            url_for("rapi.parser"),
            data = b"NET PROFIT      150      210",
            query_string={"type": "text", "spec": "ble"}
        )
        self.assertEqual(response.status_code, 400)

    @mock.patch("app.rapi.views.rutil")
    @create_and_login_user()
    def test_for_passing_text_to_parser(self, rutil):
        irec = mock.Mock()
        irec.return_value = [(("NET_PROFIT", 1), [150, 210], [0])]
        rutil.parse_text = irec

        response = self.client.post(
            url_for("rapi.parser"),
            data = b"NET PROFIT      150      210",
            query_string={"type": "text", "spec": "nls"}
        )

        self.assertTrue(irec.called)
        self.assertEqual(irec.call_args[0][1], "NET PROFIT      150      210")

    @mock.patch("app.rapi.views.rutil")
    @create_and_login_user()
    def test_for_returning_identified_records(self, rutil):
        irec = mock.Mock()
        irec.return_value = [{"name": "NET_PROFIT", "numbers": [150, 210]}]
        rutil.parse_text = irec

        response = self.client.post(
            url_for("rapi.parser"),
            data = b"NET PROFIT      150      210",
            query_string={"type": "text", "spec": "nls"}
        )
        data = response.json[0]

        self.assertEqual(data["name"], "NET_PROFIT")
        self.assertEqual(data["numbers"], [150, 210])


class FileParserTest(AppTestCase):

    def create_fake_file(self, content="Content of the file.", name="report.pdf"):
        return BytesIO(bytes(content, encoding="utf-8")), name

    @mock.patch("app.rapi.views.rutil")
    @create_and_login_user()
    def test_for_saving_file_to_disc(self, rutil):
        rutil.parse_file.return_value = {}
        data = dict(file=self.create_fake_file())
        response = self.client.post(
            url_for("rapi.parser"), data=data, 
            content_type="multipart/form-data",
            query_string={"type": "file"}
        )
        self.assertTrue(os.path.exists(
            os.path.join(self.app.config["UPLOAD_FOLDER"], data["file"][1])
        ))

    @create_and_login_user()
    def test_for_returning_400_when_no_file(self):
        response = self.client.post(
            url_for("rapi.parser"),
            content_type="multipart/form-data",
            query_string={"type": "file"}
        )
        self.assertEqual(response.status_code, 400)

    @create_and_login_user()
    def test_for_returning_400_without_name(self):
        data = dict(file=self.create_fake_file(name=""))
        response = self.client.post(
            url_for("rapi.parser"), data=data,
            content_type="multipart/form-data",
            query_string={"type": "file"}
        )
        self.assertEqual(response.status_code, 400)

    @create_and_login_user()
    def test_for_returning_400_when_file_with_not_allowed_extension(self):
        data = dict(file=self.create_fake_file(name="report.exe"))
        response = self.client.post(
            url_for("rapi.parser"), data=data,
            content_type="multipart/form-data",
            query_string={"type": "file"}
        )
        self.assertEqual(response.status_code, 400)

    @mock.patch("app.rapi.views.rutil")
    @create_and_login_user()
    def test_for_passing_filepath_to_parser(self, rutil):
        irec = mock.Mock(return_value={})
        rutil.parse_file = irec
        data = dict(file=self.create_fake_file())
        response = self.client.post(
            url_for("rapi.parser"), data=data, 
            content_type="multipart/form-data",
            query_string={"type": "file"}
        )
        self.assertTrue(irec.called)

        filepath = os.path.join(self.app.config.get("UPLOAD_FOLDER"),  
                                data["file"][1])
        self.assertEqual(irec.call_args[0][0], filepath)

    @mock.patch("app.rapi.views.rutil")
    @create_and_login_user()
    def test_response_contains_data_returned_by_parser(self, rutil):
        irec = mock.Mock(return_value={"result": "ok"})
        rutil.parse_file = irec
        data = dict(file=self.create_fake_file())
        response = self.client.post(
            url_for("rapi.parser"), data=data, 
            content_type="multipart/form-data",
            query_string={"type": "file"}
        )
        data = response.json
        self.assertEqual(data["result"], "ok")


class URLParserTest(AppTestCase):

    @mock.patch("app.rapi.views.requests.get")
    @create_and_login_user()
    def test_for_downloading_file_from_external_webpage_when_url(
        self, rget_mock
    ):
        response = self.client.post(
            url_for("rapi.parser"), data=b"http://localhost:5000/test.txt", 
            query_string={"type": "url"}
        )
        self.assertTrue(rget_mock.called)

    @mock.patch("app.rapi.views.requests.get")
    @create_and_login_user()
    def test_for_showing_alert_when_invalid_url(self, rget_mock):
        rmock = mock.Mock()
        rmock.status_code = 404
        rget_mock.return_value = rmock
        response = self.client.post(
            url_for("rapi.parser"), data=b"http://localhost:5000/test.txt", 
            query_string={"type": "url"}
        )   
        self.assertEqual(response.status_code, 400)
        
        content = response.data.decode("utf-8")
        self.assertIn("Unable to load file from given url", content)

    @mock.patch("app.rapi.views.rutil")
    @mock.patch("app.rapi.views.requests.get")
    @create_and_login_user()
    def test_for_saving_file_from_external_webpage(self, rget_mock, rutil):
        rutil.parse_file.return_value = {}
        rmock = mock.Mock()
        rmock.status_code = 200
        temp = mock.Mock()
        temp.return_value = iter([b"Test", b"report"])
        setattr(rmock, "__iter__", temp)
        rget_mock.return_value = rmock

        url = b"http://localhost:5000/test.txt"
        response = self.client.post(
            url_for("rapi.parser"), data=url, 
            query_string={"type": "url"}
        )   
        self.assertTrue(os.path.exists(
            os.path.join(self.app.config["UPLOAD_FOLDER"], 
                         str(url, encoding="utf-8").split("/")[-1])
        ))