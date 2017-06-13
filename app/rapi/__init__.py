from flask import Blueprint
from flask_restful import Api

rapi = Blueprint("rapi", __name__)
api = Api(rapi)

from app.rapi import views