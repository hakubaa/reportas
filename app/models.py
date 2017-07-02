import datetime
import sys
import inspect
import json

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import (
	Column, Integer, String, DateTime, Boolean, Float,
	UniqueConstraint, CheckConstraint
)
from sqlalchemy.inspection import inspect as sqlalchemy_inspect
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import ForeignKey
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app

from db.core import Model
from app import login_manager, db


class DBRequest(Model):
    __tablename__ = "dbrequests"
    
    id = Column(Integer, primary_key=True)
    data = Column(String, nullable=False) # data in json format

    # meta data
    model = Column(String) # model affected by data
    action = Column(String, nullable=False) # create, update, delete
    comment = Column(String) # some additional info concerning request
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", backref=backref("requests", lazy="dynamic"))
    
    # moderator_id = Column(Integer, ForeignKey("users.id"))
    # moderator = relationship("User", backref=backref("_requests", lazy="dynamic"))
    # moderated_at = Column(DateTime, default=datetime.datetime.utcnow)
    # moderator_action = Column(String)
    # moderator_comment = Column(String)
    
    __table_args__ = (
        CheckConstraint("action in ('create', 'update', 'delete')"),  
        # CheckConstraint("moderator_action in ('commit', 'reject')")
    )

    def _identify_class(self):
        for frame_info in inspect.getouterframes(inspect.currentframe()):
            try:
                return frame_info.frame.f_globals[self.model]
            except KeyError:
                pass
        return None

    def _get_session(self, session=None):
        session = session or sqlalchemy_inspect(self).session
        if not session:
            return ValueError("DBRequest requires a session")
        return session

    def _get_obj(self, id, session=None):
        cls = self._identify_class()
        if not cls:
            return NameError("model '%s' is not defined" % self.model)
        session = self._get_session(session)
        instance = session.query(cls).get(id)
        if not instance:
            return RuntimeError(
                "'%s' with id='%d' does not exist".format(self.model, id)
            )    
        return instance
    
    def execute(self, moderator, schema=None, session=None, instance=None):
        data = json.loads(self.data)
        if self.action == "create":
            return schema.load(data)
        elif self.action == "update":
            instance = instance or self._get_obj(data["id"], session)
            return schema.load(data, instance=instance, partial=True)
        elif self.action == "delete":
            instance = instance or self._get_obj(data["id"], session)
            session = self._get_session(session)
            session.delete(instance)
            return None, {}
        else:
            raise RuntimeError("action '%s' is not valid" % self.action)

    def reject(self, moderator):
        pass


class File(Model):
	__tablename__ = "files"

	id = Column(Integer, primary_key=True)
	name = Column(String(), unique=True)
	timestamp = Column(DateTime, default=datetime.datetime.utcnow)

	def __repr__(self):
		return "<File %r>" % self.name


class Permission:
    READ_DATA = 0x01
    MODIFY_DATA = 0x02
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
            "Visitor": (
                Permission.READ_DATA, False
            ),
            "User": (
                Permission.READ_DATA |
                Permission.MODIFY_DATA, True
            ),
            "Moderator": (
                Permission.READ_DATA |
                Permission.MODIFY_DATA |
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

    def add_permissions(self, perm):
        self.permissions |= perm

    def del_permissions(self, perm):
        self.permissions &= ~perm

    def __repr__(self):
        return "<Role %r>" % self.name


class User(UserMixin, Model):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(64), unique=True, index=True)
    name = Column(String(64), unique=True, index=True)
    password_hash = Column(String(128))
    confirmed = Column(Boolean, default=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)

    @property
    def password(self):
        raise AttributeError("read-only attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self, expiration=3600):
        s = Serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({"id": self.id})

    def confirm(self, token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get("id") != self.id:
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

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return None # invalid token
        user = db.session.query(User).get(data["id"])
        return user

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