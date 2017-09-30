from urllib.parse import urlparse
from flask import url_for

from tests.app import AppTestCase, create_and_login_user
from tests.app.utils import *


class IndexViewTest(AppTestCase):

    @create_and_login_user()
    def test_for_rendering_proper_template(self):
        response = self.client.get(url_for("analytics.index"))
        self.assert_template_used("analytics/index.html")
        
    def test_unauthenticated_users_are_redirected_to_login_page(self):
        response = self.client.get(url_for("analytics.index"), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for("user.login"))

    @create_and_login_user()
    def test_pass_companies_to_template(self):
        companies = [
            create_company(isin="TEST123", name="TEST123"),
            create_company(isin="TEST234", name="TEST234")
        ]
        
        response = self.client.get(url_for("analytics.index"))
        companies_wal = self.get_context_variable("companies")

        self.assertCountEqual(companies_wal, companies)


class CompanyDetailTest(AppTestCase):

    @create_and_login_user()
    def test_render_proper_template(self):
        company = create_company()
        response = self.client.get(
            url_for("analytics.ccar", company_name=company.name)
        )
        self.assert_template_used("analytics/ccar.html")

    def test_unauthenticated_users_are_redirected_to_login_page(self):
        response = self.client.get(
            url_for("analytics.ccar", company_name="fake"), 
            follow_redirects=False
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for("user.login"))

    @create_and_login_user()
    def test_redirect_to_index_page_if_company_doest_not_exist(self):
        response = self.client.get(
            url_for("analytics.ccar", company_name="test"), 
            follow_redirects=False
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            urlparse(response.location).path, 
            url_for("analytics.index")
        )

    @create_and_login_user()
    def test_pass_company_to_template(self):
        company = create_company()
        response = self.client.get(
            url_for("analytics.ccar", company_name=company.name)
        )

        company_wal = self.get_context_variable("company")

        self.assertEqual(company_wal, company)
