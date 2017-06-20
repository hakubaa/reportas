import unittest
from unittest.mock import patch

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer

from app.models import User, Role, Permission, AnonymousUser
from tests.app import AppTestCase
from app import db


class UserModelTest(unittest.TestCase):

    def test_password_setter(self):
        user = User(password="test")
        self.assertIsNotNone(user.password_hash)

    def test_password_is_read_only(self):
        user = User(password="test")
        with self.assertRaises(AttributeError):
            user.password

    def test_password_verification(self):
        user = User(password="test")
        self.assertTrue(user.verify_password("test"))
        self.assertFalse(user.verify_password("wrong"))

    def test_passwords_salts_are_random(self):
        user1 = User(password="test")
        user2 = User(password="test")
        self.assertNotEqual(user1.password_hash, user2.password_hash)

    def test_user_is_authenticated_by_default(self):
        user = User(password="test")
        self.assertTrue(user.is_authenticated)

    @patch("app.models.current_app")
    def test_for_generating_valid_confirmation_token(self, mock_app):
        mock_app.config = dict(SECRET_KEY=b'TEST')
        user = User(email="tet@test.test", id=1)
        token = user.generate_confirmation_token()
        data = Serializer(b'TEST').loads(token)
        self.assertEqual(data.get("confirm"), user.id)

    @patch("app.models.current_app")
    @patch("app.models.db")
    def test_for_confirming_account_with_token(self, db_mock, mock_app):
        mock_app.config = dict(SECRET_KEY=b'TEST')
        user = User(email="tet@test.test", id=1)
        token = user.generate_confirmation_token()
        self.assertTrue(user.confirm(token))

    @patch("app.models.current_app")
    @patch("app.models.db")
    def test_confirmation_fails_when_invalid_token(self, db_mock, mock_app):
        mock_app.config = dict(SECRET_KEY=b'TEST')
        user = User(email="tet@test.test", id=1)
        token = user.generate_confirmation_token()
        self.assertFalse(user.confirm(b"sdkfjsdfkjs.dfksdfj"))


class RoleModelTest(AppTestCase):
    
    def setUp(self):
        Role.__table__.create(db.session.bind)

    def tearDown(self):
        db.session.remove()
        Role.__table__.drop(db.session.bind)

    def test_insert_roles_creates_roles_in_db(self):
        Role.insert_roles()
        self.assertNotEqual(db.session.query(Role).count(), 0)

    def test_permissions_of_user(self):
        Role.insert_roles()
        user_role = db.session.query(Role).filter_by(name="User").one()
        self.assertTrue(user_role.permissions & Permission.READ_DATA)
        self.assertTrue(user_role.permissions & Permission.UPLOAD_DATA)

    def test_administrator_has_all_permissions(self):
        Role.insert_roles()
        admin_role = db.session.query(Role).filter_by(name="Administrator").one()
        self.assertEqual(admin_role.permissions, 0xff)


class UserRoleTest(AppTestCase):

    def test_moderator_can_moderate_data(self):
        Role.insert_roles()
        moderator = db.session.query(Role).filter_by(name="Moderator").one()
        user = User(email="mode@model.com", name="Mode", password="test",
                    role=moderator)
        db.session.add(user)
        db.session.commit()
        self.assertTrue(user.can(Permission.MODERATE_DATA))

    def test_is_administrator_returns_true_for_administrator(self):
        Role.insert_roles()
        admin = db.session.query(Role).filter_by(name="Administrator").one()
        user = User(email="mode@model.com", name="Mode", password="test",
                    role=admin)
        db.session.add(user)
        db.session.commit()
        self.assertTrue(user.is_administrator)

    def test_anonymouse_user_cannot_read_data(self):
        user = AnonymousUser()
        self.assertFalse(user.can(Permission.READ_DATA))