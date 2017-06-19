from flask import Flask
from flask_restful import Api
from flask_marshmallow import Marshmallow
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager

from app.patch.sqlalchemy import SQLAlchemy
from config import config

from db.core import Base


db = SQLAlchemy()
db.register_base(Base)

login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "user.login"


ma = Marshmallow()
debugtoolbar = DebugToolbarExtension()


def create_app(config_name):
	app = Flask(__name__)
	app.config.from_object(config[config_name])
	config[config_name].init_app(app)

	db.init_app(app)
	ma.init_app(app)
	debugtoolbar.init_app(app)
	login_manager.init_app(app)

	from app.main import main as main_blueprint
	app.register_blueprint(main_blueprint)

	from app.reports import reports as reports_blueprint
	app.register_blueprint(reports_blueprint, url_prefix="/reports")

	from app.rapi import rapi as rapi_blueprint
	app.register_blueprint(rapi_blueprint, url_prefix="/api")

	from app.user import user as user_blueprint
	app.register_blueprint(user_blueprint, url_prefix="/user")

	return app