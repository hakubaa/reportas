import unittest
from unittest.mock import patch, Mock

from crawler.models import WebPage
from crawler.engine import WebCrawler


def patch_requests_get(pass_mock=False):
    def _wrapper(func):
        def _test_method(self, res_mock):
            # res_mock.return_value = response
            def my_side_effect(*args, **kwargs):
                url = args[0]
                # Fake website for testing
                #       
                #      /> D
                #   /> B -> E
                # A        <|>
                #   \> C -> F -> G -> H
                #
                response = Mock()
                response.headers = {"Content-Type": "text/html"}
                response.encoding = "utf-8"
                if url == "http://www.page.com/":
                    response.content = b"""
                        <a href='http://www.page.com/b'>B</a>
                        <a href='http://www.page.com/c'>C</a>
                        """
                elif url == "http://www.page.com/b":
                    response.content = b"""
                        <a href='http://www.page.com/d'>D</a>
                        <a href='http://www.page.com/e'>E</a>
                        """
                elif url == "http://www.page.com/c":
                    response.content = b"""
                        <a href='http://www.page.com/f'>F</a>
                        """
                elif url == "http://www.page.com/d":
                    response.content = b"END"
                elif url == "http://www.page.com/e":
                    response.content = b"""
                        <a href='http://www.page.com/f'>F</a>
                        """
                elif url == "http://www.page.com/f":
                    response.content = b"""
                        <a href='http://www.page.com/e'>E</a>
                        <a href='http://www.page.com/g'>G</a>
                        """
                elif url == "http://www.page.com/g":
                    response.content = b"""
                        <a href='http://www.page.com/h'>H</a>
                        """
                elif url == "http://www.page.com/h":
                    response.content = b"END"
                else:
                    response.content = "PAGE NOT FOUND"
                return response

            res_mock.side_effect = my_side_effect

            if pass_mock:
                return func(self, res_mock)
            else:
                return func(self)
        return _test_method
    return _wrapper


@patch("requests.get")
class WebCrawlerTest(unittest.TestCase):
    
    @patch_requests_get()
    def test_for_visiting_all_pages(self):
        crawler = WebCrawler()
        crawler.search(WebPage("http://www.page.com/"), max_depth=100)
        self.assertEqual(len(crawler.visited), 8)

    @patch_requests_get()
    def test_for_creating_proper_map_of_website(self):
        crawler = WebCrawler()
        crawler.search(WebPage("http://www.page.com/"), max_depth=100)
        self.assertIn(
            WebPage("http://www.page.com/h"),
            crawler.webgraph[WebPage("http://www.page.com/g")]
        )
        self.assertIn(
            WebPage("http://www.page.com/h"),
            crawler.webgraph[WebPage("http://www.page.com/g")]
        )    
        self.assertIn(
            WebPage("http://www.page.com/e"),
            crawler.webgraph[WebPage("http://www.page.com/f")]
        )          
        self.assertIn(
            WebPage("http://www.page.com/f"),
            crawler.webgraph[WebPage("http://www.page.com/e")]
        )      

    @patch_requests_get()
    def test_for_calling_callback_after_visiting_page(self):
        callback = Mock()
        crawler = WebCrawler(callback=callback)
        crawler.search(WebPage("http://www.page.com/"), max_depth=0)
        self.assertTrue(callback.called)