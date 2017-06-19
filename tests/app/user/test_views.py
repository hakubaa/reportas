from flask import url_for
from flask_login import current_user

from tests.app import AppTestCase

from app import db
from app.models import User
from app.user.forms import LoginForm


class LoginViewTest(AppTestCase):

    def setUp(self): 
        User.__table__.create(db.session.bind)

    def tearDown(self): 
        db.session.remove()
        User.__table__.drop(db.session.bind)

    def test_for_rendering_correct_template(self):  
        response = self.client.get(url_for("user.login"))
        self.assert_template_used("user/login.html")

    def test_for_passing_form_to_template(self):
        response = self.client.get(url_for("user.login"))
        form = self.get_context_variable("form")
        self.assertIsInstance(form, LoginForm)

    def test_for_redirecting_after_successful_login(self):
        user = User(email="test@test.com", password="test")
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            url_for("user.login"),
            data={"email": user.email, "password": "test"}
        )

        self.assertRedirects(response, url_for("main.index"))

    def test_renders_login_template_when_login_fails(self):
        user = User(email="test@test.com", password="test")
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            url_for("user.login"),
            data={"email": user.email, "password": "test_bad"}
        )

        self.assert_template_used("user/login.html")     

    def test_for_passing_logged_in_user_to_template(self):
        user = User(email="test@test.com", password="test")
        db.session.add(user)
        db.session.commit()

        with self.client:
            response = self.client.post(
                url_for("user.login"),
                data={"email": user.email, "password": "test"}
            )
            self.assertEqual(user, current_user)

    def test_show_message_when_invalid_user_or_password(self):
        user = User(email="test@test.com", password="test")
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            url_for("user.login"),
            data={"email": user.email, "password": "test_bad"}
        )

        self.assertMessageFlashed("Invalid username or password.")     

    def test_for_redirecting_to_url_in_next_argument(self):
        user = User(email="test@test.com", password="test")
        db.session.add(user)
        db.session.commit()

        response = self.client.post(
            url_for("user.login"),
            data={"email": user.email, "password": "test"},
            query_string={"next": url_for("user.login")}
        )

        self.assertRedirects(response, url_for("user.login"))


class LogoutViewTest(AppTestCase):

    def setUp(self): 
        User.__table__.create(db.session.bind)

    def tearDown(self): 
        db.session.remove()
        User.__table__.drop(db.session.bind)

    def test_for_loging_out_the_user(self):
        user = self.create_user()
        with self.client:
            self.login_user()
            self.assertEqual(user, current_user)
            self.client.get(url_for("user.logout"))
            self.assertNotEqual(user, current_user)

    def test_for_redirecting_after_logout(self):
        self.create_user()
        self.login_user()
        response = self.client.get(url_for("user.logout"))
        self.assertRedirects(response, url_for("main.index"))

    def test_for_redirecting_to_url_in_next_argument(self):
        self.create_user()
        self.login_user()
        response = self.client.get(
            url_for("user.logout"),
            query_string={"next": url_for("user.login")}
        )
        self.assertRedirects(response, url_for("user.login"))

    def test_for_shwoing_message_after_logout(self):
        self.create_user()
        self.login_user()
        self.client.get(url_for("user.logout"))
        self.assertMessageFlashed("You have been logged out.")  