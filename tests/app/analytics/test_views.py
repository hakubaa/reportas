from urllib.parse import urlparse
from flask import url_for

from tests.app import AppTestCase, create_and_login_user


class IndexViewTest(AppTestCase):

    @create_and_login_user()
    def test_for_rendering_proper_template(self):
        response = self.client.get(url_for("analytics.index"))
        self.assert_template_used("analytics/index.html")
        
    def test_unauthenticated_users_are_redirected_to_login_page(self):
        response = self.client.get(url_for("analytics.index"), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for("user.login"))