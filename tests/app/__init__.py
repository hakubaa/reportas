import base64

from flask_testing import TestCase
from flask import url_for

from app import create_app, db
from app.models import User, Role


class NoAutoflushMeta(type):

    @staticmethod
    def turn_off_autoflush(f):
        def wrapper(*args, **kwargs):
            output = None
            with db.session.no_autoflush:
                output = f(*args, **kwargs)
            return output
        return wrapper

    def __init__(cls, name, bases, attr_dict):
        super().__init__(name, bases, attr_dict)
        for key, attr in attr_dict.items():
            if callable(attr) and key.startswith("test"):
                setattr(cls, key, NoAutoflushMeta.turn_off_autoflush(attr))


class AppTestCase(TestCase):
    models = None

    @staticmethod
    def no_autoflush(f):
        def wrapper(*args, **kwargs):
            output = None
            with db.session.no_autoflush:
                output = f(*args, **kwargs)
            return output
        return wrapper

    def create_app(self):
        return create_app("testing")

    def setUp(self):
        if self.models is None:
            db.create_all()
        else:
            for model in self.models:
                model.__table__.create(db.session.bind, checkfirst=True)
        # db.session.begin(subtransactions=True)

    def tearDown(self):
        db.session.remove()
        if self.models is None:
            db.drop_all()    
        else:
            for model in self.models:
                model.__table__.drop(db.session.bind, checkfirst=True)
        # db.session.rollback()
        # db.session.close()

    def create_user(self, email="test@test.com", name="Test", password="test"):
        Role.insert_roles()
        admin = db.session.query(Role).filter_by(name="Administrator").first()
        user = User(email=email, name=name, password=password, role=admin,
                    confirmed=True)
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

    def assertInContent(self, response, text):
        page_text = response.get_data().decode(
            encoding=response.content_encoding or "utf-8",
            errors="ignore"
        )
        self.assertIn(text, page_text)


def create_basic_httpauth_header(name, password):
    headers = {
            "Authorization": b"Basic " + base64.b64encode(
                bytes(name + ":" + password, encoding="utf-8")
            )
    }
    return headers


def create_and_login_user(pass_user=False, *, role_name="User", **udata):
    def deco_wrapper(f):
        def deco(*args, **kwargs):
            Role.insert_roles()
            admin = db.session.query(Role).filter_by(name=role_name).one() 
            user_data = {
                "email": "test@test.com",
                "name": "Test",
                "password": "test",
                "role": admin,
                "confirmed": True
            }
            user_data.update(udata)
            user = User(**user_data)
            db.session.add(user)
            db.session.commit()
            args[0].client.post(
                url_for("user.login"), 
                data=dict(email=user_data["email"], 
                          password=user_data["password"]), 
                follow_redirects=True
            )
            if pass_user:
                return f(*args, **kwargs, user=user)
            else:
                return f(*args, **kwargs)
        return deco
    return deco_wrapper