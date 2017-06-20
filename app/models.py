import datetime

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import (
	Column, Integer, String, DateTime, Boolean, Float,
	UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app

from db.core import Model
from app import login_manager, db


class File(Model):
	__tablename__ = "files"

	id = Column(Integer, primary_key=True)
	name = Column(String(), unique=True)
	timestamp = Column(DateTime, default=datetime.datetime.utcnow)

	def __repr__(self):
		return "<File %r>" % self.name


class Permission:
    READ_DATA = 0x01
    UPLOAD_DATA = 0x02
    MODERATE_DATA = 0x40 
    ADMINISTER = 0x80


class Role(Model):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    default = Column(Boolean, default=False, index=True)
    permissions = Column(Integer)
    users = relationship("User", backref="role")

    @staticmethod
    def insert_roles():
        roles = {
            "User": (
                Permission.READ_DATA |
                Permission.UPLOAD_DATA, True
            ),
            "Moderator": (
                Permission.READ_DATA |
                Permission.UPLOAD_DATA |
                Permission.MODERATE_DATA, False
            ),
            "Administrator": (0xff, False)
        }
        for role in roles:
            role_db = db.session.query(Role).filter_by(name=role).first()
            if not role_db:
                role_db = Role(name=role)
            role_db.permissions = roles[role][0]
            role_db.default = roles[role][1]
            db.session.add(role_db)
        db.session.commit()

    def __repr__(self):
        return "<Role %r>" % self.name


class User(UserMixin, Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(64), unique=True, index=True)
    name = Column(String(64), unique=True, index=True)
    password_hash = Column(String(128))
    confirmed = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("roles.id"))

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email in current_app.config.get("REPORTAS_ADMIN", []):
                self.role = db.session.query(Role).\
                                filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = db.session.query(Role).\
                                filter_by(default=True).first()

    @property
    def password(self):
        raise AttributeError("read-only attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({"confirm": self.id})

    def confirm(self, token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get("confirm") != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and \
                   (self.role.permissions & permissions) == permissions

    @property
    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def __repr__(self):
        return "<User %r>" % (self.name or self.email)
        

class AnonymousUser(AnonymousUserMixin):

    def can(self, permissions):
        return False

    def is_administrator(self):
        return False


# Flask-Login requires to set user_loader callback. This callback is used to 
# reload the user object from the user ID stored in the session. It should 
# take the unicode ID of a user, and return the corresponding user object. 
@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id))