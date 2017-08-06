import datetime
import sys
import inspect
import json

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Float,
    UniqueConstraint, CheckConstraint, and_, or_
)
from sqlalchemy.inspection import inspect as sqlalchemy_inspect
from sqlalchemy.orm import relationship, backref
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.schema import ForeignKey
from sqlalchemy.orm.properties import RelationshipProperty
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin, AnonymousUserMixin
from flask import current_app

from db.core import Model
from app import login_manager, db


class File(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String())
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User", backref=backref("files", lazy="dynamic"))

    def __repr__(self):
        return "<File %r>" % self.name


class Permission:
    BROWSE_DATA = 0x01
    CREATE_REQUESTS = 0x02
    BROWSE_REQUESTS = 0x04
    EXECUTE_REQUESTS = 0x08
    ADMINISTER = 0x16
    

class Role(Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    default = Column(Boolean, default=False, index=True)
    permissions = Column(Integer)

    @staticmethod
    def insert_roles():
        roles = {
            "Visitor": (
                Permission.BROWSE_DATA, False
            ),
            "User": (
                Permission.BROWSE_DATA |
                Permission.CREATE_REQUESTS, True
            ),
            "Moderator": (
                Permission.BROWSE_DATA |
                Permission.CREATE_REQUESTS |
                Permission.BROWSE_REQUESTS |
                Permission.EXECUTE_REQUESTS, False
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

    def has_role(self, name):
        return self.role.name.lower() == name.lower()

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
    comment = Column(String) 
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship(
        "User", backref=backref("requests", lazy="dynamic"),
        foreign_keys=(user_id,)
    )

    instance_id = Column(Integer)
    errors = Column(String)

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
        "DBRequest", 
        backref=backref(
            "parent_request", remote_side=[id], cascade="all, delete"
        )
    )

    __table_args__ = (
        CheckConstraint("action in ('create', 'update', 'delete')"),  
        CheckConstraint("moderator_action in ('accept', 'reject')")
    )
    
    def __repr__(self):
        return "DBRequest({}, {})".format(self.action, self.model)

    @property
    def executed(self):
        return self.moderator_action == "accept"

    @property
    def rejected(self):
        return self.moderator_action == "reject"

    @hybrid_property
    def outcome(self):
        if not self.executed:
            return None
        if self.errors is None or self.errors == "{}":
            return True
        else:
            return False

    @outcome.expression
    def outcome(cls):
        return and_(
            cls.moderator_action == "accept", 
            or_(cls.errors is None, cls.errors == "{}")
        )

    def add_subrequest(self, request):
        self.subrequests.append(request)

    def reject(self, moderator, comment=None):
        for request in [self] + self.subrequests:
            if not (request.executed or request.rejected):
                request.update_moderation_info(
                    moderator, action="reject", comment=comment
                )

    def execute(self, moderator, factory, comment=None):
        if self.executed:
            instance, errors = self.get_instance(
                factory.session, factory.get_model(self.model)
            )
        else:
            instance, errors = self.execute_request(
                factory, moderator, comment
            )
        
        results = []
        if not errors:
            results = self.execute_subrequests(moderator, factory, instance)
        
        return {
            "instance": instance,
            "errors": errors,
            "subrequests": results
        }
        
    def execute_subrequests(self, moderator, factory, parent_instance):
        results = [
            request.execute(moderator, factory) 
            for request in self.subrequests
        ]
        for result in results:
            if not result["errors"]:
                self.append_to_collection(parent_instance, result["instance"])   
        return results
        
    def execute_request(self, factory, moderator, comment):
        action_method = dict(
            create=self.execute_create,
            update=self.execute_update,
            delete=self.execute_delete
        )  

        data = json.loads(self.data)
        data["factory"] = factory # positional parameter for action method

        instance = None
        try:
            instance, errors = action_method[self.action](**data)
        except KeyError:
            raise RuntimeError("action '%s' is not valid" % self.action)
        except SQLAlchemyError as e:
            factory.session.rollback()
            errors = {"database": str(e.orig) }
        except Exception as e:
            factory.session.rollback()
            errors = {
                "system": "Internal system error.  If the problem persists, "
                "contact the administrator."
            }

        self.update_moderation_info(
            moderator, action="accept", comment=comment, 
            errors=errors, instance=instance
        )  

        return instance, errors

    def execute_create(self, factory, **data):
        instance, errors = factory.create(self.model, **data)
        if not errors:
            factory.session.flush()
        return instance, errors

    def execute_update(self, factory, **data):
        instance, errors = self.get_instance(
            session=factory.session, 
            model_cls=factory.get_model(self.model), id=data["id"]
        )
        if not errors:
            instance, errors = factory.update(instance, **data)   
        return instance, errors

    def execute_delete(self, factory, **data):
        instance, errors = self.get_instance(
            session=factory.session, 
            model_cls=factory.get_model(self.model), id=data["id"]
        )
        if not errors:
            factory.session.delete(instance) 
        return instance, errors

    def update_moderation_info(
        self, moderator, action, comment=None, errors=None, instance=None
    ):
        self.moderator = moderator
        self.moderator_action = action
        self.moderator_comment = comment
        self.errors = json.dumps(errors)  
        if not errors and instance:
            self.instance_id = instance.id
        self.moderated_at = datetime.datetime.utcnow()

    def get_instance(self, session, model_cls, id=None):
        instance = session.query(model_cls).get(id or self.instance_id)
        errors = dict()
        if not instance:
            errors["id"] = "Not found."
        return instance, errors

    def identify_class(self):
        for frame_info in inspect.getouterframes(inspect.currentframe()):
            try:
                return frame_info.frame.f_globals[self.model]
            except KeyError:
                pass
        return None

    def append_to_collection(self, parent_instance, child_instance):
        if parent_instance is None or child_instance is None:
            return False

        relation_attr = self.get_attr_with_relation(
            parent_instance.__class__, child_instance.__class__
        )
        if relation_attr:
            getattr(parent_instance, relation_attr).append(child_instance)
            return True

        return False

    def get_attr_with_relation(self, parent, child):
        parent_relationships = self.find_related_models(parent)
        return parent_relationships.get(child, None)

    def find_related_models(self, model_cls):
        relations = {
            prop.mapper.class_: prop.key
            for prop in model_cls.__mapper__.iterate_properties
            if isinstance(prop, RelationshipProperty)
        }
        return relations