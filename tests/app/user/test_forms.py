from tests.app import AppTestCase

from app.user.forms import LoginForm, RegistrationForm
from app.models import User
from app import db


class LoginFormTest(AppTestCase):

    def setUp(self): 
        User.__table__.create(db.session.bind)

    def tearDown(self): 
        db.session.remove()
        User.__table__.drop(db.session.bind)

    def test_validate_success_login_form(self):
        form = LoginForm(email='ad@min.com', password='admin_user')
        self.assertTrue(form.validate())

    def test_validate_invalid_email_format(self):
        form = LoginForm(email='unknown', password='example')
        self.assertFalse(form.validate())


class RegistrationFormTest(AppTestCase):

    def setUp(self): 
        User.__table__.create(db.session.bind)

    def tearDown(self): 
        db.session.remove()
        User.__table__.drop(db.session.bind)

    def test_validate_success_register_form(self):
        form = RegistrationForm(
            email="test@test.com", name="Test", password="test",
            password2="test"
        )
        self.assertTrue(form.validate())

    def test_validate_fails_when_different_passwords(self):
        form = RegistrationForm(
            email="test@test.com", name="Test", password="test",
            password2="test_bad"
        )
        self.assertFalse(form.validate())

    def test_validate_fails_not_unique_email(self):
        user = User(email="test@test.com", name="Test", password="test")
        db.session.add(user)
        db.session.commit()
        form = RegistrationForm(
            email="test@test.com", name="Testowy", password="test",
            password2="test"
        )
        self.assertFalse(form.validate())

    def test_validate_fails_not_unique_name(self):
        user = User(email="test@test.com", name="Test", password="test")
        db.session.add(user)
        db.session.commit()
        form = RegistrationForm(
            email="test@te.com", name="Test", password="test",
            password2="test"
        )
        self.assertFalse(form.validate())

    def test_name_cannot_contains_whitespaces(self):
        form = RegistrationForm(
            email="test@te.com", name="Test Test", password="test",
            password2="test"
        )
        self.assertFalse(form.validate())    