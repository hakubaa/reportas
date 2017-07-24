from flask import Flask, render_template
from flask_restful import Api
from flask_marshmallow import Marshmallow
from flask_debugtoolbar import DebugToolbarExtension
from flask_login import LoginManager
from flask_mail import Mail
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate

from app.patch.sqlalchemy import SQLAlchemy
from config import config

from db.core import Base


db = SQLAlchemy()
db.register_base(Base)

ma = Marshmallow()
debugtoolbar = DebugToolbarExtension()
mail = Mail()
login_manager = LoginManager()


def create_app(config_name, **kwargs):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    db.init_app(app)
    ma.init_app(app)
    debugtoolbar.init_app(app)
    mail.init_app(app)
    migrate = Migrate(app, db)
    Bootstrap(app)

    from app.models import AnonymousUser
    login_manager.session_protection = "strong"
    login_manager.login_view = "user.login"
    login_manager.anonymous_user = AnonymousUser
    login_manager.init_app(app)

    from app.home import home as home_blueprint
    app.register_blueprint(home_blueprint)

    from app.rapi import rapi as rapi_blueprint
    app.register_blueprint(rapi_blueprint, url_prefix="/api")

    from app.user import user as user_blueprint
    app.register_blueprint(user_blueprint, url_prefix="/user")

    from app.dbmd import dbmd
    dbmd.init_app(app, endpoint="dbmd", url="/dbmd")

    from app.dbmd.tools import dbmd_tools
    app.register_blueprint(dbmd_tools, endpoint="dmbd_tools", url_prefix="/dbmd/tools")
    
    @app.errorhandler(401)
    def unathorized_access(error):
        return render_template("401.html"), 401

    @app.errorhandler(403)
    def forbidden_access(e):
        return render_template("403.html"), 403

    return app