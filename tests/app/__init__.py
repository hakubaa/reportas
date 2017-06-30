import base64

from flask_testing import TestCase
from flask import url_for

from app import create_app, db
from app.models import User, Role


class AppTestCase(TestCase):
    models = None

    def create_app(self):
        return create_app("testing")

    def setUp(self):
        if not self.models:
            db.create_all()
        else:
            for model in self.models:
                model._table__.create(db.session.bind, checkfirst=True)

    def tearDown(self):
        if not self.models:
            db.drop_all()    
        else:
            for mode in self.models:
                model._table__.drop(db.session.bind, checkfirst=True)
        db.session.remove()

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