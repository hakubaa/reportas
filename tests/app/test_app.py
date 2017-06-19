import unittest

from flask import current_app
from app import create_app, db


class AppTestCase(unittest.TestCase):

	def setUp(self):
		self.app = create_app('testing')
		self.app_context = self.app.app_context()
		self.app_context.push()
		# db.create_all()

	def tearDown(self):
		# db.session.remove()
		# db.drop_all()
		self.app_context.pop()

	def test_db_and_session(self):
		db.create_all()
		self.assertTrue(db.session.is_active)
		from db.models import Company
		db.session.add(Company(name="TEST", isin="TEST"))
		db.session.commit()
		company = db.session.query(Company).first()
		self.assertEqual(company.name, "TEST")
		db.session.remove()
		db.drop_all()

	def test_app_exists(self):
		self.assertFalse(current_app is None)

	def test_app_is_testing(self):
		self.assertTrue(current_app.config["TESTING"])

	def test_registration_blueprint_main(self):
		self.assertIn("main", self.app.blueprints)
		from app.main import main as main_blueprint
		self.assertEqual(main_blueprint, self.app.blueprints["main"])

	def test_registration_blueprint_report(self):
		self.assertIn("reports", self.app.blueprints)
		from app.reports import reports as reports_blueprint
		self.assertEqual(reports_blueprint, self.app.blueprints["reports"])

	def test_registration_blueprint_rapi(self):
		self.assertIn("rapi", self.app.blueprints)
		from app.rapi import rapi as rapi_blueprint
		self.assertEqual(rapi_blueprint, self.app.blueprints["rapi"])

	def test_registration_blueprint_user(self):
		self.assertIn("user", self.app.blueprints)
		from app.user import user as user_blueprint
		self.assertEqual(user_blueprint, self.app.blueprints["user"])