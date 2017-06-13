from flask import url_for

from app import db
from app.rapi import api
from app.rapi.views import CompaniesListAPI, CompanyReprsListAPI
from db.models import Company, Report, CompanyRepr

from tests.app import AppTestCase


class TestCompaniesListAPI(AppTestCase):

    def test_get_requests_returns_json_response(self):
        response = self.client.get(api.url_for(CompaniesListAPI))
        self.assertEqual(response.content_type, "application/json")

    def test_get_requests_returns_list_of_companies(self):
        comp1 = Company.create(db.session, name="TEST1", isin="#TEST1")
        comp2 = Company.create(db.session, name="TEST2", isin="#TEST2")
        db.session.commit()
        response = self.client.get(api.url_for(CompaniesListAPI))
        data = response.json
        self.assertEqual(len(data), 2)

    def test_get_requests_returns_companies_data(self):
        comp = Company.create(db.session, name="TEST", isin="123#TEST")
        db.session.commit()
        response = self.client.get(api.url_for(CompaniesListAPI))
        data = response.json[0]
        self.assertEqual(data["name"], comp.name)
        self.assertEqual(data["isin"], comp.isin)

    def test_get_requests_returns_hyperlinks_to_detail_view(self):
        comp = Company.create(db.session, name="TEST", isin="123#TEST")
        CompanyRepr.create(db.session, value="TEST Repr", company=comp)
        db.session.commit()
        response = self.client.get(url_for("rapi.company_list"))
        data = response.json[0]
        self.assertIsNotNone(data["uri"])
        self.assertEqual(data["uri"], url_for("rapi.company", id=comp.id))

    def test_for_creating_company_with_post_request(self):
        response = self.client.post(
            api.url_for(CompaniesListAPI),
            data = {"name": "TEST", "isin": "TEST#ONE", "ticker": "TST" }
        )
        self.assertEqual(db.session.query(Company).count(), 1)

    def test_creates_company_with_proper_arguments(self):
        response = self.client.post(
            api.url_for(CompaniesListAPI),
            data = {"name": "TEST", "isin": "TEST#ONE", "ticker": "TST" }
        )
        company = db.session.query(Company).one()
        self.assertEqual(company.name, "TEST")
        self.assertEqual(company.isin, "TEST#ONE") 

    def test_post_request_returns_400_and_error_when_no_name(self):
        response = self.client.post(
            api.url_for(CompaniesListAPI),
            data = {"logo": "TEST", "isin": "TEST#ONE", "ticker": "TST" }
        ) 
        data = response.json
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", data)

    def test_post_request_returns_400_and_error_when_no_isin(self):
        response = self.client.post(
            api.url_for(CompaniesListAPI),
            data = {"name": "TEST", "isi": "TEST#ONE", "ticker": "TST" }
        ) 
        data = response.json
        self.assertEqual(response.status_code, 400)
        self.assertIn("isin", data)

    def test_post_request_returns_400_when_not_unique_isin(self):
        comp = Company.create(db.session, name="TEST", isin="123#TEST")
        db.session.commit()
        response = self.client.post(
            api.url_for(CompaniesListAPI),
            data = {"name": "TEST", "isin": "123#TEST", "ticker": "TST" }
        ) 
        data = response.json
        self.assertEqual(response.status_code, 400)
        self.assertIn("isin", data)


class TestCompanyAPI(AppTestCase):

    def test_get_request_returns_company_data(self):
        comp = Company.create(db.session, name="TEST1", isin="#TEST1")
        db.session.commit()
        response = self.client.get(url_for("rapi.company", id=comp.id))
        data = response.json
        self.assertEqual(data["name"], comp.name)
        self.assertEqual(data["isin"], comp.isin)

    def test_get_request_returns_404_when_company_does_not_exist(self):
        db.session.commit()
        response = self.client.get(url_for("rapi.company", id=1))       
        self.assertEqual(response.status_code, 404)

    def test_for_delating_company_with_delete_request(self):
        comp = Company.create(db.session, name="TEST1", isin="#TEST1")
        db.session.commit() 
        response = self.client.delete(url_for("rapi.company", id=comp.id))
        self.assertEqual(db.session.query(Company).count(), 0)

    def test_for_updating_company_with_put_request(self):
        comp = Company.create(db.session, name="TEST1", isin="#TEST1")
        db.session.commit()
        response = self.client.put(
            url_for("rapi.company", id=comp.id),
            data={"name": "NEW NAME", "ticker": "HEJ"}
        )
        comp = db.session.query(Company).one()
        self.assertEqual(comp.name, "NEW NAME")
        self.assertEqual(comp.ticker, "HEJ")

    def test_raises_400_when_updating_with_not_unique_isin(self):
        Company.create(db.session, name="TEST1", isin="#TEST2")
        comp = Company.create(db.session, name="TEST1", isin="#TEST1")
        db.session.commit()
        response = self.client.put(
            url_for("rapi.company", id=comp.id),
            data={"name": "NEW NAME", "isin": "#TEST2"}
        )
        self.assertEqual(response.status_code, 400)
        

class TestCompanyReprsListAPI(AppTestCase):

    def test_get_request_returns_json_response(self):
        comp = Company.create(db.session, name="TEST", isin="123#TEST")
        db.session.commit()
        response = self.client.get(
            api.url_for(CompanyReprsListAPI, id=comp.id)
        )
        self.assertEqual(response.content_type, "application/json")

    def test_get_request_returns_404_for_non_existing_company(self):
        response = self.client.get(api.url_for(CompanyReprsListAPI, id=1))
        data = response.json
        self.assertEqual(response.status_code, 404)