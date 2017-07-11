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
from sqlalchemy.orm.properties import RelationshipProperty
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app

from db.core import Model
from app import login_manager, db


class File(Model):
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
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    default = Column(Boolean, default=False, index=True)
    permissions = Column(Integer)

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
    id = Column(Integer, primary_key=True)
    email = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(64), unique=True, index=True, nullable=False)
    password_hash = Column(String(128))
    confirmed = Column(Boolean, default=False)

    role_id = Column(Integer, ForeignKey("role.id"), nullable=False)
    role = relationship("Role", backref=backref("users"))

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


class DBRequest(Model):
    id = Column(Integer, primary_key=True)
    data = Column(String, nullable=False) # data in json format

    # meta data
    model = Column(String) # model affected by data
    action = Column(String, nullable=False) # create, update, delete
    comment = Column(String) # some additional info concerning request
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship(
        "User", backref=backref("requests", lazy="dynamic"),
        foreign_keys=(user_id,)
    )
    
    errors = Column(String) # potential error when execute request in json format

    moderator_id = Column(Integer, ForeignKey("user.id"))
    moderator = relationship(
        "User", backref=backref("_requests", lazy="dynamic"),
        foreign_keys=(moderator_id,)
    )
    moderated_at = Column(DateTime)
    moderator_action = Column(String)
    moderator_comment = Column(String)
    
    parent_request_id = Column(Integer, ForeignKey("dbrequest.id"))
    subrequests = relationship(
        "DBRequest", backref=backref("parent_request", remote_side=[id])
    )

    __table_args__ = (
        CheckConstraint("action in ('create', 'update', 'delete')"),  
        CheckConstraint("moderator_action in ('accept', 'reject')")
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
        errors = dict()
        if not instance:
            errors["id"] = "Not found."
        return instance, errors

    def _update_moderation_data(
        self, moderator, action, comment=None, errors=None
    ):
        self.moderator = moderator
        self.moderator_action = action
        self.moderator_comment = comment
        self.errors = json.dumps(errors)  
        self.moderated_at = datetime.datetime.utcnow()

    def execute_create(self, factory, **data):
        return factory.create(self.model, **data)

    def execute_update(self, factory, **data):
        instance, errors = self._get_obj(data["id"], factory.session)  
        if not errors:
            instance, errors = factory.update(instance, **data)   
        return instance, errors

    def execute_delete(self, factory, **data):
        instance, errors = self._get_obj(data["id"], factory.session)
        if not errors:
            factory.session.delete(instance) 
        return instance, errors

    def execute_request(self, factory):
        action_method = dict(
            create=self.execute_create,
            update=self.execute_update,
            delete=self.execute_delete
        )  

        data = json.loads(self.data)
        data["factory"] = factory

        try:
            instance, errors = action_method[self.action](**data)
        except KeyError:
            raise RuntimeError("action '%s' is not valid" % self.action)

        return instance, errors


    def _find_related_models(self, model_cls):
        relations = {
            prop.mapper.class_: prop.key
            for prop in model_cls.__mapper__.iterate_properties
            if isinstance(prop, RelationshipProperty)
        }
        return relations

    def _get_relations_key(self, parent, child):
        parent_relationships = self._find_related_models(parent)
        return parent_relationships.get(child, None)

    def execute(self, moderator, factory, comment=None):
        parent_model = factory.get_model(self.model)
        parent_instance = None

        results = list()
        for request in [self] + self.subrequests:
            instance, errors = request.execute_request(factory)

            results.append((instance, errors))
            request._update_moderation_data(
                moderator, action="accept", comment=comment, 
                errors=errors
            )

            if not errors:
                # Add relation between objects
                if request != self:
                    request_model = factory.get_model(request.model)
                    relations_key = self._get_relations_key(
                        parent_model, request_model
                    )
                    if relations_key and parent_instance:
                        getattr(parent_instance, relations_key).append(instance)
                else:
                    parent_instance = instance
            else:
                # Stop execution when main request failed
                if request == self:
                    break

        return results

    def reject(self, moderator, comment=None):
        self._update_moderation_data(
            moderator, action="reject", comment=comment
        )
        return None, None

    def add_subrequest(self, request):
        self.subrequests.append(request)