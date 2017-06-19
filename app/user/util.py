from urllib.parse import urlparse, urljoin

from flask import request, url_for


def is_safe_url(target):
    '''Source: http://flask.pocoo.org/snippets/62/'''
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def get_redirect_target():
    '''Source: http://flask.pocoo.org/snippets/62/'''
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target