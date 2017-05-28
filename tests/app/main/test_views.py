from tests.app import AppTestCase

from app import create_app, db

from db.models import Company


class View_companies(AppTestCase):

	def test_for_using_proper_template(self):
		response = self.client.get("/companies")
		self.assert_template_used("main/companies.html")

	def test_for_passing_data_to_template(self):
		comp = Company(isin="TEST", name="TEST")
		db.session.add(comp)
		db.session.commit()
		response = self.client.get("/companies")
		data = self.get_context_variable("data")
		self.assertEqual(len(data), 1)
		self.assertEqual(data[0].name, "TEST")
		self.assertEqual(data[0].isin, "TEST")


class View_company(AppTestCase):

	def create_company(self, name="TEST", isin="TEST"):
		comp = Company(name=name, isin=isin)
		db.session.add(comp)
		db.session.commit()
		return comp

	def test_for_using_proper_templates(self):
		company = self.create_company()
		response = self.client.get("/companies/TEST")
		self.assert_template_used("main/company.html")

	def test_for_passing_data_to_template(self):
		company = self.create_company()
		response = self.client.get("/companies/TEST")
		data = self.get_context_variable("data")
		self.assertIsInstance(data, Company)
		self.assertEqual(data.name, "TEST")

	def test_for_404_when_invalid_isin(self):
		response = self.client.get("/companies/INVALID")
		self.assertTrue(response.status_code, 404)

	def test_for_using_proper_template_when_404(self):
		response = self.client.get("/companies/INVALID")
		self.assert_template_used("404.html")