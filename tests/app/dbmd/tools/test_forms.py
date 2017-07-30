from app.dbmd.tools.forms import ReportUploaderForm, DirectInputForm
from db.models import Company
from app import db

from tests.app import AppTestCase, create_and_login_user


def create_company(name, isin):
    company = Company(name=name, isin=isin)
    db.session.add(company)
    db.session.commit()
    return company


class ReportUploaderFormTest(AppTestCase):

    def test_populate_company_select_field_with_companies(self):
        company1 = create_company("JAGO", "@JAGO")
        company2 = create_company("OS", "@OS")

        form = ReportUploaderForm()

        choices = list(form.company.iter_choices())
        self.assertEqual(len(choices), 3)
        self.assertIn(company1.name, choices[1])
        self.assertIn(company2.name, choices[2])

    def test_required_fields(self):
        form = ReportUploaderForm()

        form.validate()

        self.assertTrue(form.errors)
        self.assertIn("file", form.errors)


class DirectInputFormTest(AppTestCase):

    def test_required_fields(self):
        form = DirectInputForm()

        form.validate()

        self.assertTrue(form.errors)
        self.assertIn("company", form.errors)
        self.assertIn("content", form.errors)


    def test_populate_company_select_field_with_companies(self):
        company1 = create_company("JAGO", "@JAGO")
        company2 = create_company("OS", "@OS")

        form = DirectInputForm()

        choices = list(form.company.iter_choices())
        self.assertEqual(len(choices), 2)
        self.assertIn(company1.name, choices[0])
        self.assertIn(company2.name, choices[1])