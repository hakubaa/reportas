from tests.app import AppTestCase

from app.user.forms import LoginForm
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