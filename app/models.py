import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import (
	Column, Integer, String, DateTime, Boolean, Float,
	UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey
from flask_login import UserMixin

from db.core import Model
from app import login_manager, db


class File(Model):
	__tablename__ = "files"

	id = Column(Integer, primary_key=True)
	name = Column(String(), unique=True)
	timestamp = Column(DateTime, default=datetime.datetime.utcnow)

	def __repr__(self):
		return "<File %r>" % self.name


class Role(Model):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    users = relationship("User", backref="role")

    def __repr__(self):
        return "<Role %r>" % self.name


class User(UserMixin, Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(64), unique=True, index=True)
    name = Column(String(64), unique=True, index=True)
    password_hash = Column(String(128))
    role_id = Column(Integer, ForeignKey("roles.id"))

    @property
    def password(self):
        raise AttributeError("read-only attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return "<User %r>" % (self.name or self.email)
        

# Flask-Login requires to set user_loader callback. This callback is used to 
# reload the user object from the user ID stored in the session. It should 
# take the unicode ID of a user, and return the corresponding user object. 
@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(int(user_id))