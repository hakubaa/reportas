import base64
import unittest.mock as mock
from urllib.parse import urlparse

from flask import url_for
from flask_login import current_user

from tests.app import AppTestCase, create_basic_httpauth_header

from app import db
from app.models import User, Role
from app.user.forms import LoginForm, RegistrationForm


class LoginViewTest(AppTestCase):

    def test_for_rendering_correct_template(self):  
        response = self.client.get(url_for("user.login"))
        self.assert_template_used("user/login.html")

    def test_for_passing_form_to_template(self):
        response = self.client.get(url_for("user.login"))
        form = self.get_context_variable("form")
        self.assertIsInstance(form, LoginForm)

    def test_for_redirecting_after_successful_login(self):
        user = self.create_user()

        response = self.client.post(
            url_for("user.login"),
            data={"email": user.email, "password": "test"}
        )

        self.assertRedirects(response, url_for("home.homepage"))

    def test_renders_login_template_when_login_fails(self):
        user = self.create_user()

        response = self.client.post(
            url_for("user.login"),
            data={"email": user.email, "password": "test_bad"}
        )

        self.assert_template_used("user/login.html")     

    def test_for_passing_logged_in_user_to_template(self):
        user = self.create_user()

        with self.client:
            response = self.client.post(
                url_for("user.login"),
                data={"email": user.email, "password": "test"}
            )
            self.assertEqual(user, current_user)

    def test_show_message_when_invalid_user_or_password(self):
        user = self.create_user()

        response = self.client.post(
            url_for("user.login"),
            data={"email": user.email, "password": "test_bad"}
        )

        self.assertMessageFlashed("Invalid username or password.")     

    def test_for_redirecting_to_url_in_next_argument(self):
        user = self.create_user()

        response = self.client.post(
            url_for("user.login"),
            data={"email": user.email, "password": "test"},
            query_string={"next": url_for("user.login")}
        )

        self.assertRedirects(response, url_for("user.login"))


class LogoutViewTest(AppTestCase):

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
        self.assertRedirects(response, url_for("home.homepage"))

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


class RegistrationViewTest(AppTestCase):

    def setUp(self): 
        super().setUp()
        Role.insert_roles()

    def test_for_rendering_correct_template(self):  
        response = self.client.get(url_for("user.register"))
        self.assert_template_used("user/register.html")

    def test_for_passing_form_to_template(self):
        response = self.client.get(url_for("user.register"))
        form = self.get_context_variable("form")
        self.assertIsInstance(form, RegistrationForm)

    def test_for_redirecting_to_login_page_after_registration(self):
        response = self.client.post(
            url_for("user.register"),
            data={
                "email": "test@test.com", "password": "test",
                "name": "Test", "password2": "test"
            }
        )
        self.assertRedirects(response, url_for("user.login"))

    def test_for_creating_new_user(self):
        self.client.post(
            url_for("user.register"),
            data={
                "email": "test@test.com", "password": "test",
                "name": "Test", "password2": "test"
            }
        )   
        self.assertEqual(db.session.query(User).count(), 1)
        user = db.session.query(User).one()
        self.assertEqual(user.name, "Test")

    def test_new_user_is_not_confirmed_by_default(self):
        self.client.post(
            url_for("user.register"),
            data={
                "email": "test@test.com", "password": "test",
                "name": "Test", "password2": "test"
            }
        )   
        user = db.session.query(User).one()
        self.assertFalse(user.confirmed)


class ConfirmationViewTest(AppTestCase):

    def test_for_confirming_user_with_valid_token(self):
        user = self.create_user()
        token = user.generate_token()
        self.login_user()
        response = self.client.get(
            url_for("user.confirm", token=token),
            follow_redirects=False
        )
        user = db.session.query(User).one()
        self.assertTrue(user.confirmed)

    def test_redirects_user_to_main_page_when_invalid_token(self):
        user = self.create_user()
        token = user.generate_token()
        self.login_user()
        response = self.client.get(url_for("user.confirm", token="abc.abc"))
        self.assertRedirects(response, url_for("home.homepage"))

    def test_unauthenticated_user_are_redirected_to_login_page(self):
        user = self.create_user()
        token = user.generate_token()
        response = self.client.get(url_for("user.confirm", token=token))
        self.assertEqual(urlparse(response.location).path, url_for("user.login"))


class AuthorizationTest(AppTestCase):

    def test_returns_unauthorized_access_for_not_authenticated_user(self):
        response = self.client.get(url_for("user.get_token"))
        self.assertEqual(response.status_code, 401)

    def test_authenticate_user_with_http_authentication(self):
        user = self.create_user()
        response = self.client.get(
            url_for("user.get_token"),
            headers=create_basic_httpauth_header(user.email, "test")
        )
        self.assertEqual(response.status_code, 200)

    def test_authenticate_user_with_cookie_based_authentication(self):
        user = self.create_user()
        self.login_user()
        response = self.client.get(url_for("user.get_token"))
        self.assertEqual(response.status_code, 200)

    def test_for_receiving_token(self):
        user = self.create_user()
        self.login_user()
        response = self.client.get(url_for("user.get_token"))
        data = response.json
        self.assertIn("token", data)

    def test_auathetnicate_user_with_token(self):
        user = self.create_user()
        db.session.add(user)
        db.session.commit()
        token = user.generate_token()
        response = self.client.get(
            url_for("user.get_token"),
            headers={
                "Authorization": b"OpenStock " + token
            }
        )        
        self.assertEqual(response.status_code, 200)