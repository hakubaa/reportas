from app.dbmd.tools.forms import (
    ReportUploaderForm, DirectInputForm, BatchUploaderForm
)
# from db import models
# from app import db

from tests.app import AppTestCase, create_and_login_user
from tests.app.dbmd.tools.utils import (
    create_company, create_ftype, create_fschema
)


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


class BatchUploaderFormTest(AppTestCase):

    def test_required_fields(self):
        form = BatchUploaderForm()

        form.validate()

        self.assertTrue(form.errors)
        self.assertIn("fschema", form.errors)

    def test_populate_fschema_select_field_with_schemas(self):
        ftype = create_ftype("bls")
        schema1 = create_fschema(ftype=ftype, value="FSCHEMA#1")
        schema2 = create_fschema(ftype=ftype, value="FSCHEMA#2")

        form = BatchUploaderForm()

        choices = list(form.fschema.iter_choices())
        self.assertEqual(len(choices), 2)
        self.assertIn(schema1.default_repr.value, choices[0])
        self.assertIn(schema2.default_repr.value, choices[1])