import unittest

from app.models import User


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