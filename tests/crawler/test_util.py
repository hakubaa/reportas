import unittest
from unittest.mock import patch, Mock

from bs4 import BeautifulSoup

from crawler import util


class FindWithReTest(unittest.TestCase):

    def test_for_finding_email_addresses(self):
        content = "BlaBla test@test.com amazing 'admin@test.com'"
        emails = list(util.find_with_re(content, util.RE_EMAIL))
        self.assertEqual(len(emails), 2)
        self.assertEqual(emails[0], "test@test.com")
        self.assertEqual(emails[1], "admin@test.com")

    def test_for_finding_urls(self):
        content = """"
        This page 'http://www.awesome.com' is awesome. But this one
        https://www.notawesome.pl is not.
         """
        urls = list(util.find_with_re(content, util.RE_URL))
        self.assertEqual(len(urls), 2)
        self.assertEqual(urls[0], "http://www.awesome.com")

    def test_for_finding_urls_with_bs(self):
        content = """
        <html><head><title>Test Page</title></head>
        <body>
            <h1>My Favourite Web Pages</h1>
            <ul>
                <li><a href="http://www.google.com">Google</a></li>
                <li><a>No Href</a></li>
                <li><a href="www.sport.com">Sport</a></li>
            </ul>
        </body>

        """
        soup = BeautifulSoup(content, "html.parser")
        urls = list(util.find_with_bs(soup, tag="a", attr="href"))
        self.assertEqual(len(urls), 3)
        self.assertCountEqual(["http://www.google.com", None, "www.sport.com"],
                              urls)


class FilterWithReTest(unittest.TestCase):

    def test_returns_iterable_with_matching_elements(self):
        test_iter = [ "test.com", "http://test.com", "www.invalid.org" ]
        result = list(util.filter_with_re(test_iter, r".*test.*"))
        self.assertEqual(len(result), 2)
        self.assertCountEqual(test_iter[:2], result)

    def test_returns_empty_iterable_if_no_item_match_pattern(self):
        test_iter = [ "abc", "def", "ghg" ]
        result = list(util.filter_with_re(test_iter, r"^test.*"))
        self.assertFalse(result)