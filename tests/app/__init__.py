import base64

from flask_testing import TestCase
from flask import url_for

from app import create_app, db
from app.models import User


class AppTestCase(TestCase):

    def create_app(self):
        return create_app("testing")

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def create_user(self, email="test@test.com", name="Test", password="test"):
        user = User(email=email, name=name, password=password)
        db.session.add(user)
        db.session.commit()
        return user

    def login_user(self, email="test@test.com", password="test"):
        return self.client.post(
            url_for("user.login"), 
            data=dict(email=email, password=password), 
            follow_redirects=True
        )

    def logout_user(self):
        return self.client.get(url_for("user.logout"), follow_redirects=True)


def create_basic_httpauth_header(name, password):
    headers = {
            "Authorization": b"Basic " + base64.b64encode(
                bytes(name + ":" + password, encoding="utf-8")
            )
    }
    return headers