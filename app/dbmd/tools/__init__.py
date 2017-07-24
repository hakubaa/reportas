from flask import Blueprint

dbmd_tools = Blueprint("dbmd_tools", __name__)

from app.dbmd.tools import views