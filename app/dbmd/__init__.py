from flask import Blueprint

# dbmd - database management dashboard
dbmd = Blueprint("dbmd", __name__)

from app.dbmd import views