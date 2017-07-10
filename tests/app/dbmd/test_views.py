import base64
import json
import unittest.mock as mock
from urllib.parse import urlparse

from flask import url_for
from flask_login import current_user

from tests.app import AppTestCase, create_and_login_user

from app import db
from app.models import User, DBRequest
# from app.dbmd.forms import CompanyForm
import db.models as models


class IndexViewTest(AppTestCase):
    
    @create_and_login_user()
    def test_for_rendering_proper_template(self):
        response = self.client.get(url_for("admin.index"))
        self.assert_template_used("admin/index.html")
        
    def test_unauthenticated_users_are_redirected_to_login_page(self):
        response = self.client.get(url_for("admin.index"), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for("user.login"))

    
class ListCompaniesViewTest(AppTestCase):
    
    @create_and_login_user()
    def test_for_rendering_proper_template(self):
        response = self.client.get(url_for("company.index_view"))
        self.assert_template_used("admin/model/list.html") 
        
    @create_and_login_user()
    def test_for_displaying_companies_data(self):
        company1 = models.Company(isin="ISIN TEST", name="TEST")
        company2 = models.Company(isin="ISIN TEST #123", name="TEST2")
        db.session.add_all((company1, company2))
        db.session.commit()
        
        response = self.client.get(url_for("company.index_view"))
        
        self.assertInContent(response, company1.isin)
        self.assertInContent(response, company2.isin)

    def test_unauthenticated_users_are_redirected_to_login_page(self):
        response = self.client.get(url_for("company.index_view"), 
                                   follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for("user.login"))


class CreateCompanyViewTest(AppTestCase):
    
    @create_and_login_user()
    def test_for_rendering_proper_template(self):
        response = self.client.get(url_for("company.create_view"))
        self.assert_template_used("admin/model/create.html")    
        
    @create_and_login_user(pass_user=True)
    def test_post_request_with_all_data_creates_new_dbrequest(self, user=True):
        response = self.client.post(
            url_for("company.create_view"),
            data = dict(name="TEST", isin="#TEST", ticker="TICKER")
        )
        
        self.assertEqual(db.session.query(models.Company).count(), 0)
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "create")
        
        data = json.loads(dbrequest.data)
        self.assertEqual(data["isin"], "#TEST")
        self.assertEqual(data["ticker"], "TICKER")
        
    @create_and_login_user()
    def test_redirects_after_successful_post_request(self):
        response = self.client.post(
            url_for("company.create_view"),
            data = dict(name="TEST", isin="#TEST", ticker="TICKER")
        ) 
        self.assertRedirects(response, url_for("company.index_view"))
        
    @create_and_login_user()
    def test_form_populate_controls_after_unsuccessful_request(self):
        response = self.client.post(
            url_for("company.create_view"),
            data = dict(name="OPENSTOCK", ticker="TICKER#123")
        ) 
        form = self.get_context_variable("form")
        self.assertInContent(response, "TICKER#123")
        self.assertInContent(response, "OPENSTOCK")


class UpdateCompanyViewTest(AppTestCase):
    
    def create_company(self, isin="#TEST", name="TEST"):
        company = models.Company(isin=isin, name=name)
        db.session.add(company)
        db.session.commit()
        return company
        
    @create_and_login_user()
    def test_for_rendering_proper_template(self):
        company = self.create_company()
        response = self.client.get(url_for("company.edit_view", id=company.id))
        self.assert_template_used("admin/model/edit.html")
        
    @create_and_login_user()
    def test_redirects_to_list_view_when_company_does_not_exist(self):
        response = self.client.get(url_for("company.edit_view", id=1),
                                   follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for("company.index_view"), response.location)

    @create_and_login_user()  
    def test_form_is_populated_with_data_of_edited_object(self):
        company = self.create_company()
        response = self.client.get(url_for("company.edit_view", id=company.id))
        form = self.get_context_variable("form")
        self.assertEqual(form.name.data, company.name)
        self.assertEqual(form.isin.data, company.isin)
        
    @create_and_login_user(pass_user=True)
    def test_post_request_with_all_data_creates_new_dbrequest(self, user=True):
        company = self.create_company()
        response = self.client.post(
            url_for("company.edit_view", id=company.id),
            data = dict(name="NEW NAME", isin=company.isin)
        )
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "update")
        
        data = json.loads(dbrequest.data)
        self.assertEqual(data["name"], "NEW NAME")
        self.assertEqual(data["id"], company.id)
        
    @create_and_login_user()
    def test_redirects_after_successful_post_request(self):
        company = self.create_company()
        response = self.client.post(
            url_for("company.edit_view", id=company.id),
            data = dict(name="NEW NAME", isin=company.isin),
            follow_redirects=False
        )
        self.assertRedirects(response, url_for("company.index_view"))
        
    @create_and_login_user()
    def test_form_populate_controls_after_unsuccessful_request(self):
        company = self.create_company()
        response = self.client.post(
            url_for("company.edit_view", id=company.id),
            data = dict(name=None, ticker="TICKER#123")
        )
        form = self.get_context_variable("form")
        self.assertInContent(response, "TICKER#123")


class DeleteCompanyViewTest(AppTestCase):
    
    def create_company(self, isin="#TEST", name="TEST"):
        company = models.Company(isin=isin, name=name)
        db.session.add(company)
        db.session.commit()
        return company

    @create_and_login_user()
    def test_redirects_to_list_view_when_company_does_not_exist(self):
        response = self.client.post(url_for("company.delete_view", id=1),
                                   follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for("company.index_view"), response.location)

    @create_and_login_user(pass_user=True)
    def test_for_creating_dbrequest(self, user=True):
        company = self.create_company()
        response = self.client.post(
            url_for("company.delete_view", id=company.id)
        )
        
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "delete")
        
        data = json.loads(dbrequest.data)
        self.assertEqual(data["id"], company.id)
        
    @create_and_login_user()
    def test_redirects_after_request(self):
        company = self.create_company()
        response = self.client.post(
            url_for("company.delete_view", id=company.id),
            follow_redirects=False
        )
        self.assertRedirects(response, url_for("company.index_view"))
    

# class CompanyDetailViewTest(AppTestCase):

#     def create_company(self, name="TEST", isin="#TEST"):
#         company = models.Company(name=name, isin=isin)
#         db.session.add(company)
#         db.session.commit()
#         return company

#     @create_and_login_user()
#     def test_for_rendering_proper_template(self):
#         company = self.create_company()
        
#         self.client.get(url_for("dbmd.company_detail", id=company.id))
        
#         self.assert_template_used("dbmd/companies/company_detail.html") 
        
#     @create_and_login_user()
#     def test_for_passing_companies_to_template(self):
#         company = self.create_company()
        
#         self.client.get(url_for("dbmd.company_detail", id=company.id))
        
#         company_ref = self.get_context_variable("company")
#         self.assertEqual(company, company_ref)

#     @create_and_login_user
#     def test_for_rendering_404_when_company_does_not_exist(self):
#         self.client.get(url_for("dbmd.company_detail", id=1))
        
#         self.assert_template_used("dbmd/404.html") 