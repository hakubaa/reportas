import unittest
from unittest.mock import patch
import json

from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from marshmallow_sqlalchemy import ModelSchema

from app.models import User, Role, Permission, AnonymousUser, DBRequest
from tests.app import AppTestCase
from app import db, ma

from db import records_factory
from db.core import Model

################################################################################
# CREATE ADDITIONAL MODELS & METHODS FOR TESTS
################################################################################

class Student(Model):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    age = Column(Integer)
    name = Column(String, nullable=False)


class Account(Model):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    balance = Column(Integer, default=0)

    student_id = Column(Integer, ForeignKey("students.id"))
    student = relationship("Student", backref="accounts")


@records_factory.register_schema()
class StudentSchema(ModelSchema):
    class Meta:
        model = Student


@records_factory.register_schema()
class AccountSchema(ModelSchema):
    class Meta:
        model = Account


def create_related_requests(session, user, data={"name": "Python", "age": 17}):
    main_request = DBRequest(
        model="Student", user=user, action="create", data=json.dumps(data)
    )
    subrequest = DBRequest(
        model="Account", user=user, action="create",
        data=json.dumps({"balance": 100})
    )
    session.add_all((main_request, subrequest))
    main_request.add_subrequest(subrequest)
    session.commit()
    return main_request, subrequest
    
################################################################################


class DBRequestTest(AppTestCase):
    models = [DBRequest, Student, User, Role, Account]

    def setUp(self):
        super().setUp()
        records_factory.session = db.session
        Role.insert_roles()

    def create_user(self, email="test@test.com", password="test",
                    role_name="User", name="Test"):
        role = db.session.query(Role).filter_by(name=role_name).one()
        user = User(email=email, password=password, role=role, name=name)
        db.session.add(user)
        db.session.commit()
        return user

    def test_create_new_object_with_dbrequest(self):
        user = self.create_user()
        dbrequest = DBRequest(
            model="Student", user=user, action="create",
            comment="Create new student",
            data=json.dumps({"age": 17, "name": "Python"})
        )
        obj, errors = dbrequest.execute(user, records_factory)[0]
        db.session.add(obj)
        self.assertTrue(db.session.query(Student).count(), 1)

    def test_update_object_with_dbrequest(self):
        user = self.create_user()
        student = Student(age=17, name="Python 2")
        db.session.add(student)
        db.session.commit()
        dbrequest = DBRequest(
            model="Student", user=user, action="update",
            comment="Create new student",
            data=json.dumps({"age": 18, "name": "Python 3", "id": student.id})
        )    
        obj, errors = dbrequest.execute(user, records_factory)[0]
        db.session.commit()
        student = db.session.query(Student).one()
        self.assertEqual(student.age, 18)
        self.assertEqual(student.name, "Python 3")

    def test_delete_object_with_dbrequest(self):
        user = self.create_user()
        student = Student(age=17, name="Python 2")
        db.session.add(student)
        db.session.commit()
        dbrequest = DBRequest(
            model="Student", user=user, action="delete",
            comment="Create new student",
            data=json.dumps({"id": student.id})
        )    
        obj, errors = dbrequest.execute(user, records_factory)[0]
        db.session.commit()
        self.assertEqual(db.session.query(Student).count(), 0)

    def test_identify_class_returns_class_object(self):
        user = self.create_user()
        dbrequest = DBRequest(
            model="Student", user=user, action="create",
            comment="Create new student",
            data=json.dumps({"age": 17, "name": "Python"})
        )
        cls = dbrequest._identify_class()
        self.assertEqual(cls, Student)

    def test_identify_class_returns_None_when_class_does_not_exist(self):
        user = self.create_user()
        dbrequest = DBRequest(
            model="Studentos", user=user, action="create",
            comment="Create new student",
            data=json.dumps({"age": 17, "name": "Python"})
        )
        cls = dbrequest._identify_class()
        self.assertIsNone(cls)

    def test_errors_are_saved_in_dbrequest(self):
        user = self.create_user()
        dbrequest = DBRequest(
            model="Student", user=user, action="create",
            data=json.dumps({"age": 17})
        )
        db.session.add(dbrequest)
        obj, errors = dbrequest.execute(user, records_factory)[0]
        self.assertIsNotNone(dbrequest.errors)
        errors_request = json.loads(dbrequest.errors)
        self.assertIn("name", errors_request)
        self.assertEqual(errors_request["name"], errors["name"])

    def test_execute_updates_information_about_moderator(self):
        user = self.create_user()
        moderator = self.create_user(email="moderator@test.com", name="Moder")
        dbrequest = DBRequest(
            model="Student", user=user, action="create",
            data=json.dumps({"age": 17, "name": "Python"})
        )
        db.session.add(dbrequest)
        obj, errors = dbrequest.execute(moderator, records_factory, comment="ok")[0]
        self.assertFalse(errors) # make sure there are no errors
        
        self.assertEqual(dbrequest.moderator, moderator)
        self.assertEqual(dbrequest.moderator_action, "accept")
        self.assertEqual(dbrequest.moderator_comment, "ok")

    def test_reject_updates_information_about_moderator(self):
        user = self.create_user()
        moderator = self.create_user(email="moderator@test.com", name="Moder")
        dbrequest = DBRequest(
            model="Student", user=user, action="create",
            data=json.dumps({"age": 17, "name": "Python"})
        )
        db.session.add(dbrequest)
        obj, errors = dbrequest.reject(
            moderator=moderator, comment="no this time"
        )
        self.assertFalse(errors) # make sure there are no errors
        
        self.assertEqual(dbrequest.moderator, moderator)
        self.assertEqual(dbrequest.moderator_action, "reject")
        self.assertEqual(dbrequest.moderator_comment, "no this time") 
        
    def test_update_request_returns_error_when_invalid_id(self):
        user = self.create_user()
        student = Student(age=17, name="Python 2")
        db.session.add(student)
        db.session.commit()
        dbrequest = DBRequest(
            model="Student", user=user, action="update",
            comment="Create new student",
            data=json.dumps({"age": 18, "id": student.id + 1})
        )    
        obj, errors = dbrequest.execute(user, records_factory)[0]
        self.assertTrue(errors)
        self.assertIn("id", errors)
        
    def test_delete_request_returns_error_when_invalid_id(self):
        user = self.create_user()
        student = Student(age=17, name="Python 2")
        db.session.add(student)
        db.session.commit()
        dbrequest = DBRequest(
            model="Student", user=user, action="delete",
            data=json.dumps({"id": student.id + 1})
        )    
        obj, errors = dbrequest.execute(user, records_factory)[0]
        self.assertTrue(errors)
        self.assertIn("id", errors)

    def test_add_subrequest_appends_dependent_request_to_main_request(self):
        user = self.create_user()
        
        main_request, subrequest = create_related_requests(db.session, user)
        
        self.assertEqual(len(main_request.subrequests), 1)
        self.assertEqual(main_request.subrequests[0], subrequest)
        self.assertEqual(subrequest.parent_request, main_request)
        
    def test_execute_executes_subrequests(self):
        user = self.create_user()
        main_request, subrequest = create_related_requests(db.session, user)
        
        main_request.execute(user, records_factory)
       
        self.assertEqual(db.session.query(Student).count(), 1)
        self.assertEqual(db.session.query(Account).count(), 1)

    def test_execute_creates_relation_with_subrequests(self):
        user = self.create_user()
        main_request, subrequest = create_related_requests(db.session, user)
        
        main_request.execute(user, records_factory)    
        
        student = db.session.query(Student).one()
        account = db.session.query(Account).one()

        self.assertIn(account, student.accounts)
        self.assertEqual(account.student, student)   

    def test_request_execution_stops_when_main_request_fails(self):
        user = self.create_user()
        main_request, subrequest = create_related_requests(
            db.session, user, data={"age": 17} # noe name
        ) 

        results = main_request.execute(user, records_factory)

        self.assertIn("name", results[0][1])
        self.assertEqual(db.session.query(Student).count(), 0)
        self.assertEqual(db.session.query(Account).count(), 0)


class UserModelTest(unittest.TestCase):

    def test_password_setter(self):
        user = User(password="test")
        self.assertIsNotNone(user.password_hash)

    def test_password_is_read_only(self):
        user = User(password="test")
        with self.assertRaises(AttributeError):
            user.password

    def test_password_verification(self):
        user = User(password="test")
        self.assertTrue(user.verify_password("test"))
        self.assertFalse(user.verify_password("wrong"))

    def test_passwords_salts_are_random(self):
        user1 = User(password="test")
        user2 = User(password="test")
        self.assertNotEqual(user1.password_hash, user2.password_hash)

    def test_user_is_authenticated_by_default(self):
        user = User(password="test")
        self.assertTrue(user.is_authenticated)

    @patch("app.models.current_app")
    def test_for_generating_valid_confirmation_token(self, mock_app):
        mock_app.config = dict(SECRET_KEY=b'TEST')
        user = User(email="tet@test.test", id=1, name="Test")
        token = user.generate_token()
        data = Serializer(b'TEST').loads(token)
        self.assertEqual(data.get("id"), user.id)

    @patch("app.models.current_app")
    @patch("app.models.db")
    def test_for_confirming_account_with_token(self, db_mock, mock_app):
        mock_app.config = dict(SECRET_KEY=b'TEST')
        user = User(email="tet@test.test", id=1, name="Test")
        token = user.generate_token()
        self.assertTrue(user.confirm(token))

    @patch("app.models.current_app")
    @patch("app.models.db")
    def test_confirmation_fails_when_invalid_token(self, db_mock, mock_app):
        mock_app.config = dict(SECRET_KEY=b'TEST')
        user = User(email="tet@test.test", id=1, name="Test")
        token = user.generate_token()
        self.assertFalse(user.confirm(b"sdkfjsdfkjs.dfksdfj"))


class RoleModelTest(AppTestCase):
    
    def setUp(self):
        Role.__table__.create(db.session.bind)

    def tearDown(self):
        db.session.remove()
        Role.__table__.drop(db.session.bind)

    def test_insert_roles_creates_roles_in_db(self):
        Role.insert_roles()
        self.assertNotEqual(db.session.query(Role).count(), 0)

    def test_permissions_of_user(self):
        Role.insert_roles()
        user_role = db.session.query(Role).filter_by(name="User").one()
        self.assertTrue(user_role.permissions & Permission.READ_DATA)
        self.assertTrue(user_role.permissions & Permission.MODIFY_DATA)

    def test_administrator_has_all_permissions(self):
        Role.insert_roles()
        admin_role = db.session.query(Role).filter_by(name="Administrator").one()
        self.assertEqual(admin_role.permissions, 0xff)


class UserRoleTest(AppTestCase):

    def test_moderator_can_moderate_data(self):
        Role.insert_roles()
        moderator = db.session.query(Role).filter_by(name="Moderator").one()
        user = User(email="mode@model.com", name="Mode", password="test",
                    role=moderator)
        db.session.add(user)
        db.session.commit()
        self.assertTrue(user.can(Permission.MODERATE_DATA))

    def test_is_administrator_returns_true_for_administrator(self):
        Role.insert_roles()
        admin = db.session.query(Role).filter_by(name="Administrator").one()
        user = User(email="mode@model.com", name="Mode", password="test",
                    role=admin)
        db.session.add(user)
        db.session.commit()
        self.assertTrue(user.is_administrator)

    def test_anonymouse_user_cannot_read_data(self):
        user = AnonymousUser()
        self.assertFalse(user.can(Permission.READ_DATA))