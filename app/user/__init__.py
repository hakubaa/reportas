from flask import Blueprint, g

user = Blueprint("user", __name__)

from app.user.auth import auth
from app.user import views