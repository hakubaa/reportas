import types
import functools

from flask import g, request, current_app, make_response
from flask_httpauth import HTTPBasicAuth, HTTPTokenAuth, MultiAuth
from flask_login import current_user

from app.models import User
from app import db


class MixMultiAuth(MultiAuth):

    def login_required(self, f):
        http_auth = MultiAuth.login_required(self, f)
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            # Cookie based authentication
            if not current_app.login_manager._login_disabled \
                    and current_user.is_authenticated:
                g.user = current_user # http_auth also sets g.user
                return f(*args, **kwargs)
            # Http authentication
            return http_auth(*args, **kwargs)
        return decorated


basic_auth = HTTPBasicAuth()
token_auth = HTTPTokenAuth("OpenStock")
auth = MixMultiAuth(basic_auth, token_auth)


@basic_auth.verify_password
def verify_password(email, password):
    user = db.session.query(User).filter_by(email=email).first()
    if not user or not user.verify_password(password):
        return False
    g.user = user
    return True


@token_auth.verify_token
def verify_token(token):
    user = User.verify_auth_token(token)
    if not user:
        return False
    g.user = user
    return True