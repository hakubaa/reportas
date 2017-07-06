from flask import Blueprint

home = Blueprint("home", __name__)

from app.home import views

from app.models import Permission

@home.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)