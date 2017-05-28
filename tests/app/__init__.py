from flask_testing import TestCase

from app import create_app, db


class AppTestCase(TestCase):

	def create_app(self):
		return create_app("testing")

	def setUp(self):
		db.create_all()

	def tearDown(self):
		db.session.remove()
		db.drop_all()
