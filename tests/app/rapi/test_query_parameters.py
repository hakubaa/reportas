from datetime import datetime
import json

from flask import url_for
import dateutil
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import backref, relationship

from app import db, ma
from app.rapi import rapi
from app.rapi.base import ListView
from app.rapi.util import DatetimeEncoder
from app.models import User, Role
from db.core import Model

from tests.app import AppTestCase, create_and_login_user


################################################################################
# CREATE MODELS FOR TESTS
################################################################################

class Student(Model):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    age = Column(Integer)
    name = Column(String)

class EMail(Model):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True)
    value = Column(String)

    student_id = Column(Integer, ForeignKey("students.id"))
    student = relationship("Student", backref=backref("emails", lazy="joined"))

class StudentSchema(ma.ModelSchema):
    class Meta:
        model = Student

class EMailSchema(ma.ModelSchema):
    class Meta:
        model = EMail

class StudentListView(ListView):
    model = Student
    schema = StudentSchema

class StudentEmailListView(ListView):
    model = EMail
    schema = EMailSchema

    def get_objects(self, id):
        student = db.session.query(Student).get(id)
        if not student:
            abort(404)
        return student.emails


rapi.add_url_rule(
    "/students",  
    view_func=StudentListView.as_view("student_list")
)
rapi.add_url_rule(
    "/students/<int:id>/emails",
    view_func=StudentEmailListView.as_view("student_email_list")
)

################################################################################

class BaseQueryTest(AppTestCase):
    models = (Student, EMail, User, Role)

    def create_students(self):
        db.session.add_all([
            Student(name="Anna", age=10),
            Student(name="Python", age=20),
            Student(name="Java", age=15),
            Student(name="Anna", age=3)
        ])

    @create_and_login_user()
    def test_get_request_returns_list_of_students(self):
        self.create_students()
        response = self.client.get(url_for("rapi.student_list"))
        data = response.json
        self.assertEqual(data["count"], 4)

    @create_and_login_user()
    def test_restrict_returned_fields(self):
        self.create_students()
        response = self.client.get(
            url_for("rapi.student_list"),
            query_string={"fields": "name"},
        )
        data = response.json["results"]
        self.assertNotIn("age", data[0])
        self.assertNotIn("id", data[0])
        self.assertIn("name", data[0])

    @create_and_login_user()
    def test_sort_records(self):
        self.create_students()
        response = self.client.get(
            url_for("rapi.student_list"),
            query_string={"sort": "age"},
        )
        data = response.json["results"]
        self.assertEqual(data[0]["age"], 3)
        self.assertEqual(data[1]["age"], 10)
        self.assertEqual(data[2]["age"], 15)
        self.assertEqual(data[3]["age"], 20)

    @create_and_login_user()
    def test_sort_records_by_two_columns(self):
        self.create_students()
        response = self.client.get(
            url_for("rapi.student_list"),
            query_string={"sort": "-name, age"},
        )
        data = response.json["results"]
        self.assertEqual(data[3]["age"], 10)
        self.assertEqual(data[3]["name"], "Anna")

    @create_and_login_user()
    def test_sort_records_in_reverse_order(self):
        self.create_students()
        response = self.client.get(
            url_for("rapi.student_list"),
            query_string={"sort": "-age"},
        )
        data = response.json["results"]
        self.assertEqual(data[3]["age"], 3)
        self.assertEqual(data[2]["age"], 10)
        self.assertEqual(data[1]["age"], 15)
        self.assertEqual(data[0]["age"], 20)   

    @create_and_login_user()
    def test_limit_number_of_returned_records(self):
        self.create_students()
        response = self.client.get(
            url_for("rapi.student_list"),
            query_string={"limit": 2}
        )
        data = response.json
        self.assertEqual(data["count"], 2)

    @create_and_login_user()
    def test_offset_returned_records(self):
        self.create_students()
        response = self.client.get(
            url_for("rapi.student_list"),
            query_string={"offset": 2, "sort": "age"}
        )
        data = response.json
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["results"][0]["age"], 15)


class ListTest(AppTestCase):
    models = (Student, EMail, User, Role)

    def create_student_with_emails(self):
        student = Student(name="Python", age=20)
        db.session.add(student)
        student.emails.append(EMail(value="bbbbbb@python.is.the.best"))
        student.emails.append(EMail(value="aaaaaa@python.is.the.best"))
        student.emails.append(EMail(value="cccccc@python.is.the.best"))
        db.session.commit()
        return student

    @create_and_login_user()
    def test_limit_number_of_returned_records(self):
        student = self.create_student_with_emails()
        response = self.client.get(
            url_for("rapi.student_email_list", id=student.id),
            query_string={"limit": 1}
        )
        data = response.json
        self.assertEqual(data["count"], 1)


    @create_and_login_user()
    def test_sort_records(self):
        student = self.create_student_with_emails()
        response = self.client.get(
            url_for("rapi.student_email_list", id=student.id),
            query_string={"limit": 1000, "sort": "value"}
        )
        data = response.json["results"]
        self.assertEqual(data[0]["value"], "aaaaaa@python.is.the.best")
        self.assertEqual(data[1]["value"], "bbbbbb@python.is.the.best")
        self.assertEqual(data[2]["value"], "cccccc@python.is.the.best")

    @create_and_login_user()
    def test_offset_returned_records(self):
        student = self.create_student_with_emails()
        response = self.client.get(
            url_for("rapi.student_email_list", id=student.id),
            query_string={"offset": 2, "sort": "-value"}
        )
        data = response.json
        self.assertEqual(data["count"], 1)
        self.assertEqual(
            data["results"][0]["value"], "aaaaaa@python.is.the.best"
        )

    @create_and_login_user()
    def test_restrict_returned_fields(self):
        student = self.create_student_with_emails()
        response = self.client.get(
            url_for("rapi.student_email_list", id=student.id),
            query_string={"offset": 2, "sort": "-value", "fields": "id"}
        )
        data = response.json["results"]
        self.assertNotIn("value", data[0])
        self.assertIn("id", data[0])