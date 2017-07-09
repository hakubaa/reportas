from tests.app import AppTestCase

from app.dbmd.forms import CompanyForm, RecordTypeForm, RecordTypeReprForm
from app.models import User
from app import db
import db.models as models


class CompanyFormTest(AppTestCase):

    def create_company(self, name="TEST", isin="#TEST"):
        company = models.Company(name=name, isin=isin)
        db.session.add(company)
        db.session.commit()
        return company

    def test_validate_fails_when_no_isin(self):
        form = CompanyForm(name="TEST")
        validate_outcome = form.validate()
        self.assertFalse(validate_outcome)
        self.assertIn("isin", form.errors)
        
    def test_validate_fails_when_no_name(self):
        form = CompanyForm(isin="#TEST")
        validate_outcome = form.validate()
        self.assertFalse(validate_outcome)
        self.assertIn("name", form.errors)
        
    def test_validate_succeeds_when_isin_and_name_are_present(self):
        form = CompanyForm(name="TEST", isin="#TEST")
        validate_outcome = form.validate()
        self.assertTrue(validate_outcome)
        self.assertFalse(form.errors)
        
    def test_validate_fails_when_isin_is_not_unique(self):
        company = self.create_company()
        
        form = CompanyForm(isin="#TEST", name="NEW_NAME")
        validate_outcome = form.validate()
        
        self.assertFalse(validate_outcome)
        self.assertIn("isin", form.errors)
    
    def test_validate_fails_when_name_is_not_unique(self):
        company = self.create_company()

        form = CompanyForm(
            isin=company.isin, name=company.name, ticker="TEST"
        )
        validate_outcome = form.validate()
        
        self.assertFalse(validate_outcome)

    def test_edit_mode_turns_off_validation_of_uniqueness(self):
        company = self.create_company()   

        form = CompanyForm(
            isin=company.isin, name=company.name, ticker="TEST",
            edit_mode=True
        )
        validate_outcome = form.validate()

        self.assertTrue(validate_outcome)    
        
    def test_for_populating_object_with_data_from_form(self):
        '''It should work for every form. Just testing this functionality.'''
        company = self.create_company()
        
        form = CompanyForm(ticker="TST", fullname="TEST OF FORM")
        form.populate_obj(company)
        
        self.assertEqual(company.ticker, "TST")
        self.assertEqual(company.fullname, "TEST OF FORM")


class RecordTypeFormTest(AppTestCase):

    def test_validate_fails_when_no_statement(self):
        form = RecordTypeForm(name="TEST")
        validate_outcome = form.validate()
        self.assertFalse(validate_outcome)
        self.assertIn("statement", form.errors)
        
    def test_validate_fails_when_no_name(self):
        form = RecordTypeForm(statement="bls")
        validate_outcome = form.validate()
        self.assertFalse(validate_outcome)
        self.assertIn("name", form.errors)

    def test_validate_fails_when_isin_is_not_unique(self):
        company = models.RecordType(name="TEST", statement="bls")
        db.session.add(company)
        db.session.commit()
        
        form = RecordTypeForm(name="TEST", statement="cfs")
        validate_outcome = form.validate()
        
        self.assertFalse(validate_outcome)
        self.assertIn("name", form.errors)

    def test_validate_fails_when_statement_not_from_choices(self):
        form = RecordTypeForm(name="TEST", statement="ble")

        validate_outcome = form.validate()

        self.assertFalse(validate_outcome)
        self.assertIn("statement", form.errors)


class RecordTypeReprFormTest(AppTestCase):

    def create_rtype(self, name="TEST", statement="bls"):
        rtype = models.RecordType(name=name, statement=statement)
        db.session.add(rtype)
        db.session.commit()
        return rtype

    def test_validate_fails_when_no_lang(self):
        form = RecordTypeReprForm(value="TEST")

        validate_outcome = form.validate()

        self.assertFalse(validate_outcome)
        self.assertIn("lang", form.errors)
        
    def test_validate_fails_when_no_value(self):
        form = RecordTypeReprForm(lang="PL")

        validate_outcome = form.validate()

        self.assertFalse(validate_outcome)
        self.assertIn("value", form.errors)

    def test_validate_fails_when_no_rtype(self):
        form = RecordTypeReprForm(lang="PL", value="TEST")

        validate_outcome = form.validate()

        self.assertFalse(validate_outcome)
        self.assertIn("rtype", form.errors)

    def test_validate_fails_when_rtype_not_from_db(self):
        rtype = models.RecordType(name="TEST", statement="bls")
        form = RecordTypeReprForm(lang="PL", value="TEST", rtype=rtype)

        validate_outcome = form.validate()

        self.assertFalse(validate_outcome)
        self.assertIn("rtype", form.errors)

    def test_validate_succeeds_when_rtype_from_db(self):
        rtype = self.create_rtype()
        form = RecordTypeReprForm(lang="PL", value="TEST", rtype=rtype)

        validate_outcome = form.validate()

        self.assertTrue(validate_outcome)