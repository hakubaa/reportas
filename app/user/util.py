from threading import Thread
from urllib.parse import urlparse, urljoin

from flask import request, url_for, current_app, render_template
from flask_mail import Message

from app import mail


def is_safe_url(target):
    '''Source: http://flask.pocoo.org/snippets/62/'''
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
           ref_url.netloc == test_url.netloc


def get_redirect_target():
    '''Source: http://flask.pocoo.org/snippets/62/'''
    target = request.values.get("next")
    if not target:
        return None
    if is_safe_url(target):
        return target


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, async=False, **kwargs):
    msg = Message(
        subject, sender=current_app.config["MAIL_USERNAME"], recipients=[to]
    )
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    if async:
        thr = Thread(target=send_async_email, args=[current_app, msg])
        thr.start()
        return thr
    else:
        mail.send(msg)