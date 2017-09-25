from datetime import datetime
import json
import unittest
from unittest import mock
import operator

from flask import url_for
import dateutil
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import backref, relationship

from app import db, ma
from app.rapi import rapi
from app.rapi.base import (
    ListView, FlaskRequestParamsReader, SortQueryModyfier,
    SliceQueryModifier, FilterQueryModifier, SortListModyfier,
    SliceListModifier, FilterListModifier
)
from app.rapi.utils import QueryFilter, apply_conversion
from app.models import User, Role, DBRequest
from db.core import Model
from app.rapi.utils import apply_conversion

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
    priority = Column(Integer, default=0)

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


def create_students():
    db.session.add_all([
        Student(name="Anna", age=10),
        Student(name="Python", age=20),
        Student(name="Java", age=15),
        Student(name="Anna", age=3)
    ])

def create_student(name, age):
    student = Student(name=name, age=age)
    db.session.add(student)
    db.session.commit()
    return student


################################################################################

class QPTest(AppTestCase):
    models = (Student, EMail, User, Role, DBRequest)

    @create_and_login_user()
    def test_get_request_returns_list_of_students(self):
        create_students()
        response = self.client.get(url_for("rapi.student_list"))
        data = response.json
        self.assertEqual(data["count"], 4)

    @create_and_login_user()
    def test_restrict_returned_fields(self):
        create_students()
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
        create_students()
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
        create_students()
        response = self.client.get(
            url_for("rapi.student_list"),
            query_string={"sort": "-name, age"},
        )
        data = response.json["results"]
        self.assertEqual(data[3]["age"], 10)
        self.assertEqual(data[3]["name"], "Anna")

    @create_and_login_user()
    def test_sort_records_in_reverse_order(self):
        create_students()
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
        create_students()
        response = self.client.get(
            url_for("rapi.student_list"),
            query_string={"limit": 2}
        )
        data = response.json
        self.assertEqual(data["count"], 2)

    @create_and_login_user()
    def test_offset_returned_records(self):
        create_students()
        response = self.client.get(
            url_for("rapi.student_list"),
            query_string={"offset": 2, "sort": "age"}
        )
        data = response.json
        self.assertEqual(data["count"], 2)
        self.assertEqual(data["results"][0]["age"], 15)

    @create_and_login_user()
    def test_create_many_objects_simultaneously(self):
        response = self.client.post(
            url_for("rapi.student_list"),
            data = json.dumps([
                {"age": 17, "name": "Python"},
                {"age": 18, "name": "Noe"},
                {"age": 19, "name": "Joe"}
            ]),
            query_string={"many": "T"}
        )
        self.assertEqual(response.status_code, 202)
        dbrequests = db.session.query(DBRequest).all()
        self.assertEqual(len(dbrequests), 3)
        names = [ json.loads(req.data)["name"] for req in dbrequests ]
        self.assertCountEqual(names, ["Python", "Noe", "Joe"])

    @create_and_login_user()
    def test_update_many_objects_simultaneously(self):
        students = (
            Student(name="Python", age=17),
            Student(name="Neo", age=18),
            Student(name="Joe", age=19)
        )
        db.session.add_all(students)
        db.session.commit()
        response = self.client.put(
            url_for("rapi.student_list"),
            data = json.dumps([
                {"id": student.id, "age": student.age + 1}
                for student in students
            ]),
            query_string={"many": "TRUE"}
        )
        self.assertEqual(response.status_code, 202)
        dbrequests = db.session.query(DBRequest).all()
        self.assertEqual(len(dbrequests), 3)
        names = [ json.loads(req.data)["age"] for req in dbrequests ]
        self.assertCountEqual(names, [18, 19, 20])

    @create_and_login_user()
    def test_delete_many_objects_simultaneously(self):
        students = (
            Student(name="Python", age=17),
            Student(name="Neo", age=18),
            Student(name="Joe", age=19)
        )
        db.session.add_all(students)
        db.session.commit()
        response = self.client.delete(
            url_for("rapi.student_list"),
            data = json.dumps([{"id": student.id} for student in students]),
            query_string={"many": "TRUE"}
        )
        self.assertEqual(response.status_code, 202)
        dbrequests = db.session.query(DBRequest).all()
        self.assertEqual(len(dbrequests), 3)
        names = [ json.loads(req.data)["id"] for req in dbrequests ]
        self.assertCountEqual(names, [student.id for student in students])    


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


class FilterTest(AppTestCase):
    models = (Student, EMail, User, Role)

    def create_five_students(self):
        return [ 
            create_student(name="Student%d" % i, age=i) 
            for i in range(5) 
        ]

    def assertFilter(self, qfilter, results):
        students = db.session.query(Student).filter(qfilter).all()
        self.assertCountEqual(students, results)  

    @create_and_login_user()
    def test_filter_students_by_age_test01(self):
        students = self.create_five_students()

        response = self.client.get(
            url_for("rapi.student_list"),
            query_string={"filter": "age=1"}
        )
        data = response.json["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Student1")
        self.assertEqual(data[0]["age"], 1)

    @create_and_login_user()
    def test_filter_students_by_age_test02(self):
        students = self.create_five_students()

        response = self.client.get(
            url_for("rapi.student_list"),
            query_string={"filter": "age>1"}
        )
        data = response.json["results"]

        self.assertEqual(len(data), 3)
        self.assertEqual(min(map(lambda item: item["age"], data)), 2)

    @create_and_login_user()
    def test_combine_different_filters(self):
        students = self.create_five_students()

        response = self.client.get(
            url_for("rapi.student_list"),
            query_string={"filter": "age>1;name=%s"%students[2].name},
        )
        data = response.json["results"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Student2")
        self.assertEqual(data[0]["age"], 2)

    @create_and_login_user()
    def test_filter_emails_by_priority(self):
        student = create_student(name="Python", age=18)
        student.emails.append(EMail(value="Test", priority=0))
        student.emails.append(EMail(value="Help", priority=10))
        student.emails.append(EMail(value="Question", priority=5))

        response = self.client.get(
            url_for("rapi.student_email_list", id=student.id),
            query_string={"filter": "priority>2"}
        )
        data = response.json
        
        self.assertEqual(data["count"], 2)

    @create_and_login_user()
    def test_filter_emails_by_priority_and_in_operator(self):
        student = create_student(name="Python", age=18)
        student.emails.append(EMail(value="Test", priority=0))
        student.emails.append(EMail(value="Help", priority=10))
        student.emails.append(EMail(value="Question", priority=5))

        response = self.client.get(
            url_for("rapi.student_email_list", id=student.id),
            query_string={"filter": "priority@in@5,10"}
        )
        data = response.json
        
        self.assertEqual(data["count"], 2)


#-------------------------------------------------------------------------------
# Refactored Views
#-------------------------------------------------------------------------------

class StudentExtListView(ListView):
    model = Student
    schema = StudentSchema
    
    filter_columns = ["name"] # only this columns can be filtered


class CrazyQueryFilter(QueryFilter):
    
    def modify_column(self, field):
        return "age"
        

class StudentCrazyListView(ListView):
    model = Student
    schema = StudentSchema
    
    filter_overrides = {
        "name": [
            CrazyQueryFilter(
                operator="=", method_query=operator.eq,
                method_list=apply_conversion(operator.eq)
            )
        ]
    }

class CrazyEmailFilter(QueryFilter):
    
    def modify_value(self, value):
        return "-1"
        

class StudentEmailListView(ListView):
    model = EMail
    schema = EMailSchema
    
    filter_overrides = {
        "priority": [
            CrazyEmailFilter(
                operator=">", method_query=operator.ge,
                method_list=apply_conversion(operator.ge)
            )
        ]
    }

    def get_objects(self, id):
        student = db.session.query(Student).get(id)
        if not student:
            abort(404)
        return student.emails
        

rapi.add_url_rule(
    "/students_ext",
    view_func=StudentExtListView.as_view("student_ext_list")
)

rapi.add_url_rule(
    "/students_crazy",
    view_func=StudentCrazyListView.as_view("student_crazy_list")
)

rapi.add_url_rule(
    "/students_crazy/<int:id>/emails",
    view_func=StudentEmailListView.as_view("student_crazy_email_list")
)

class ModyfiedFilterTest(AppTestCase):
    models = (Student, EMail, User, Role)

    def create_five_students(self):
        return [ 
            create_student(name="Student%d" % i, age=i) 
            for i in range(5) 
        ]
        
    @create_and_login_user()
    def test_cannot_filter_with_columns_not_being_in_the_list(self):
        students = self.create_five_students()

        response = self.client.get(
            url_for("rapi.student_ext_list"),
            query_string={"filter": "age=1"}
        )
        data = response.json["results"]

        self.assertEqual(len(data), 5)
        
    @create_and_login_user()
    def test_can_filter_with_columns_from_the_list(self):
        students = self.create_five_students()
        
        response = self.client.get(
            url_for("rapi.student_ext_list"),
            query_string={"filter": "name=Student1"}
        )
        data = response.json["results"]

        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["age"], 1)
        self.assertEqual(data[0]["name"], "Student1")
        
    @create_and_login_user()
    def test_default_filters_can_be_overridden(self):
        students = self.create_five_students()
        
        response = self.client.get(
            url_for("rapi.student_crazy_list"),
            query_string={"filter": "name=2"}
        )
        data = response.json["results"]
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["age"], 2)
        self.assertEqual(data[0]["name"], "Student2")
        
    @create_and_login_user()
    def test_overidden_filters_without_defined_operators_are_omitted(self):
        students = self.create_five_students()
        
        response = self.client.get(
            url_for("rapi.student_crazy_list"),
            query_string={"filter": "name%in%2"}
        )
        data = response.json["results"]
        
        self.assertEqual(len(data), 5)

   
    @create_and_login_user()
    def test_not_overriden_filters_working_conventionally(self):
        students = self.create_five_students()
        
        response = self.client.get(
            url_for("rapi.student_crazy_list"),
            query_string={"filter": "age=3"}
        )
        data = response.json["results"]
        
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["age"], 3)
        self.assertEqual(data[0]["name"], "Student3")
        
    @create_and_login_user()
    def test_overridden_filter_works_for_list(self):
        student = create_student(name="Python", age=18)
        student.emails.append(EMail(value="Test", priority=0))
        student.emails.append(EMail(value="Help", priority=10))
        student.emails.append(EMail(value="Question", priority=5))
        
        response = self.client.get(
            url_for("rapi.student_crazy_email_list", id=student.id),
            query_string={"filter": "priority>5"}
        )
        data = response.json
        
        self.assertEqual(data["count"], 3)
        
#-------------------------------------------------------------------------------



@mock.patch(
    "app.rapi.base.request", 
    args=dict(filter="name=JAGO;age=5", sort="-age,name", limit=10, offset=5)
)
class FlaskRequestParamsReaderTest(unittest.TestCase):

    def test_read_filter_params(self, request):
        params_reader = FlaskRequestParamsReader()

        params = params_reader.get_filter_params()

        self.assertEqual(len(params), 2)
        self.assertEqual(params[0], "name=JAGO")
        self.assertEqual(params[1], "age=5")

    def test_read_sort_params(self, request):
        params_reader = FlaskRequestParamsReader()

        params = params_reader.get_sort_params()

        self.assertEqual(len(params), 2)
        self.assertEqual(params[0], "-age")
        self.assertEqual(params[1], "name")

    def test_read_slice_params(self, request):
        params_reader = FlaskRequestParamsReader()

        params = params_reader.get_slice_params()

        self.assertIn("limit", params)
        self.assertIn("offset", params)
        self.assertEqual(params["limit"], 10)
        self.assertEqual(params["offset"], 5)

    def test_get_all_params_simultaneously(self, request):
        params_reader = FlaskRequestParamsReader()

        params = params_reader.get_params()

        self.assertEqual(len(params["filter"]), 2)
        self.assertEqual(params["filter"][0], "name=JAGO")
        self.assertEqual(len(params["sort"]), 2)
        self.assertEqual(params["sort"][0], "-age")
        self.assertEqual(params["limit"], 10)
        self.assertEqual(params["offset"], 5)

    def test_parse_no_params(self, request):
        request.args = dict()

        params_reader = FlaskRequestParamsReader()

        params = params_reader.get_params()

        self.assertEqual(len(params["filter"]), 0)
        self.assertEqual(len(params["sort"]), 0)
        self.assertEqual(params["limit"], None)
        self.assertEqual(params["offset"], None)



class SortQueryModyfiersTest(AppTestCase):

    def setUp(self):
        super().setUp()
        self.students = [
            Student(name="Anna", age=10),
            Student(name="Python", age=20),
            Student(name="Java", age=15),
            Student(name="Anna", age=3)
        ]
        db.session.add_all(self.students)
        db.session.commit()

    def test_sort_query_by_single_field(self):
        query = db.session.query(Student)
        qmod = SortQueryModyfier()

        query = qmod.apply(query, ["name"])
        students = query.all()

        self.assertEqual(len(students), 4)
        
        names = [ item.name for item in students ]
        self.assertEqual(names, ["Anna", "Anna", "Java", "Python"])

    def test_sort_query_by_single_field_in_descending_order(self):
        query = db.session.query(Student)
        qmod = SortQueryModyfier()

        query = qmod.apply(query, ["-name"])
        students = query.all()

        self.assertEqual(len(students), 4)
        
        names = [ item.name for item in students ]
        self.assertEqual(names, ["Python", "Java", "Anna", "Anna"])

    def test_sort_by_multiple_fields(self):
        query = db.session.query(Student)
        qmod = SortQueryModyfier()

        query = qmod.apply(query, ["name", "age"])
        students = query.all()

        self.assertEqual(len(students), 4)
        
        names = [ item.name for item in students ]
        self.assertEqual(names, ["Anna", "Anna", "Java", "Python"])

        ages = [ item.age for item in students ]
        self.assertEqual(ages, [3, 10, 15, 20])

    def test_invalid_field_is_ignored(self):
        query = db.session.query(Student)
        qmod = SortQueryModyfier()

        query = qmod.apply(query, ["name", "city"])
        students = query.all()

        self.assertEqual(len(students), 4)
        
        names = [ item.name for item in students ]
        self.assertEqual(names, ["Anna", "Anna", "Java", "Python"])


class SliceQueryModifierTest(AppTestCase):

    def setUp(self):
        super().setUp()
        self.students = [
            Student(name="Anna", age=10),
            Student(name="Python", age=20),
            Student(name="Java", age=15),
            Student(name="Anna", age=3)
        ]
        db.session.add_all(self.students)
        db.session.commit()

    def test_limit_number_of_returned_items(self):
        query = db.session.query(Student)
        qmod = SliceQueryModifier()

        query = qmod.apply(query, limit=2)
        students = query.all()

        self.assertEqual(len(students), 2)

    def test_offset_returned_items(self):
        query = db.session.query(Student)
        qmod = SliceQueryModifier()

        query = qmod.apply(query, offset=2)
        students = query.all()

        self.assertEqual(len(students), 2)  

    def test_apply_limit_and_offset_together(self): 
        query = db.session.query(Student).order_by(Student.age)
        qmod = SliceQueryModifier()

        query = qmod.apply(query, offset=2, limit=1)
        students = query.all()

        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].name, "Java")  


class FilterQueryModifierTest(AppTestCase):

    def setUp(self):
        super().setUp()
        self.students = [
            Student(name="Anna", age=10),
            Student(name="Python", age=20),
            Student(name="Java", age=15),
            Student(name="Anna", age=3)
        ]
        db.session.add_all(self.students)
        db.session.commit()

        self.filters = [
            QueryFilter(operator="=", method_query=operator.eq),
            QueryFilter(operator="<=", method_query=operator.le),
            QueryFilter(operator="<", method_query=operator.lt),
            QueryFilter(operator="!=", method_query=operator.ne),
            QueryFilter(operator=">=", method_query=operator.ge),
            QueryFilter(operator=">", method_query=operator.gt)
        ]

    def test_filter_by_single_field_and_eq_operator(self):
        query = db.session.query(Student)
        qmod = FilterQueryModifier(self.filters)

        query = qmod.apply(query, ["age=20"])
        students = query.all()

        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].name, "Python")


    def test_filter_by_single_field_and_gt_operator(self):
        query = db.session.query(Student)
        qmod = FilterQueryModifier(self.filters)

        query = qmod.apply(query, ["age>10"])
        students = query.all()

        self.assertEqual(len(students), 2)

        ages = [ item.age for item in students ]
        self.assertCountEqual(ages, [15, 20])

    def test_filter_by_multiple_fields(self):
        query = db.session.query(Student)
        qmod = FilterQueryModifier(self.filters)

        query = qmod.apply(query, ["age>5", "name=Anna"])
        students = query.all()

        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].age, 10)

    def test_invalid_fields_are_ignored(self):        
        query = db.session.query(Student)
        qmod = FilterQueryModifier(self.filters)

        query = qmod.apply(query, ["age>5", "username=Anna"])
        students = query.all()

        self.assertEqual(len(students), 3)

    def test_limit_columns_used_in_filtering(self):
        query = db.session.query(Student)
        qmod = FilterQueryModifier(self.filters, columns=["age"])

        query = qmod.apply(query, ["age>5", "name=Anna"])
        students = query.all()

        self.assertEqual(len(students), 3)

    def test_override_default_operators(self):
        query = db.session.query(Student)

        class Age2NameFilter(QueryFilter):
            
            def modify_column(self, column):
                return "name"

        qmod = FilterQueryModifier(
            self.filters, overrides=dict(age=[
                Age2NameFilter(operator="=", method_query=operator.eq)
            ])
        )

        query = qmod.apply(query, ["age=Anna"])
        students = query.all()

        self.assertEqual(len(students), 2)


class SortListModyfiersTest(AppTestCase):

    def setUp(self):
        super().setUp()
        self.students = [
            Student(name="Anna", age=10),
            Student(name="Python", age=20),
            Student(name="Java", age=15),
            Student(name="Anna", age=3)
        ]
        db.session.add_all(self.students)
        db.session.commit()

    def test_sort_query_by_single_field(self):
        items = db.session.query(Student).all()
        qmod = SortListModyfier()

        students = qmod.apply(items, ["name"])

        self.assertEqual(len(students), 4)
        
        names = [ item.name for item in students ]
        self.assertEqual(names, ["Anna", "Anna", "Java", "Python"])

    def test_sort_query_by_single_field_in_descending_order(self):
        items = db.session.query(Student).all()
        qmod = SortListModyfier()

        students = qmod.apply(items, ["-name"])

        self.assertEqual(len(students), 4)
        
        names = [ item.name for item in students ]
        self.assertEqual(names, ["Python", "Java", "Anna", "Anna"])

    def test_sort_by_multiple_fields(self):
        items = db.session.query(Student).all()
        qmod = SortListModyfier()

        students = qmod.apply(items, ["name", "age"])

        self.assertEqual(len(students), 4)
        
        names = [ item.name for item in students ]
        self.assertEqual(names, ["Anna", "Anna", "Java", "Python"])

        ages = [ item.age for item in students ]
        self.assertEqual(ages, [3, 10, 15, 20])

    def test_invalid_field_is_ignored(self):
        items = db.session.query(Student).all()
        qmod = SortListModyfier()

        students = qmod.apply(items, ["name", "city"])

        self.assertEqual(len(students), 4)
        
        names = [ item.name for item in students ]
        self.assertEqual(names, ["Anna", "Anna", "Java", "Python"])


class SliceListModifierTest(AppTestCase):

    def setUp(self):
        super().setUp()
        self.students = [
            Student(name="Anna", age=10),
            Student(name="Python", age=20),
            Student(name="Java", age=15),
            Student(name="Anna", age=3)
        ]
        db.session.add_all(self.students)
        db.session.commit()

    def test_limit_number_of_returned_items(self):
        items = db.session.query(Student).all()
        qmod = SliceListModifier()

        students = qmod.apply(items, limit=2)

        self.assertEqual(len(students), 2)

    def test_offset_returned_items(self):
        items = db.session.query(Student).all()
        qmod = SliceListModifier()

        students = qmod.apply(items, offset=2)

        self.assertEqual(len(students), 2)  

    def test_apply_limit_and_offset_together(self): 
        items = db.session.query(Student).order_by(Student.age)
        qmod = SliceListModifier()

        students = qmod.apply(items, offset=2, limit=1)

        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].name, "Java")  


class FilterListModifierTest(AppTestCase):

    def setUp(self):
        super().setUp()
        self.students = [
            Student(name="Anna", age=10),
            Student(name="Python", age=20),
            Student(name="Java", age=15),
            Student(name="Anna", age=3)
        ]
        db.session.add_all(self.students)
        db.session.commit()

        self.filters = [
            QueryFilter(operator="=", method_query=apply_conversion(operator.eq)),
            QueryFilter(operator="<=", method_query=apply_conversion(operator.le)),
            QueryFilter(operator="<", method_query=apply_conversion(operator.lt)),
            QueryFilter(operator="!=", method_query=apply_conversion(operator.ne)),
            QueryFilter(operator=">=", method_query=apply_conversion(operator.ge)),
            QueryFilter(operator=">", method_query=apply_conversion(operator.gt))
        ]

    def test_filter_by_single_field_and_eq_operator(self):
        items = db.session.query(Student).all()
        qmod = FilterListModifier(self.filters)

        students = qmod.apply(items, ["age=20"])

        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].name, "Python")

    def test_filter_by_single_field_and_gt_operator(self):
        items = db.session.query(Student).all()
        qmod = FilterListModifier(self.filters)

        students = qmod.apply(items, ["age>10"])

        self.assertEqual(len(students), 2)

        ages = [ item.age for item in students ]
        self.assertCountEqual(ages, [15, 20])

    def test_filter_by_multiple_fields(self):
        items = db.session.query(Student).all()
        qmod = FilterListModifier(self.filters)

        students = qmod.apply(items, ["age>5", "name=Anna"])

        self.assertEqual(len(students), 1)
        self.assertEqual(students[0].age, 10)

    def test_invalid_fields_are_ignored(self):        
        items = db.session.query(Student).all()
        qmod = FilterListModifier(self.filters)

        students = qmod.apply(items, ["age>5", "username=Anna"])

        self.assertEqual(len(students), 3)

    def test_limit_columns_used_in_filtering(self):
        items = db.session.query(Student).all()
        qmod = FilterListModifier(self.filters, columns=["age"])

        students = qmod.apply(items, ["age>5", "name=Anna"])

        self.assertEqual(len(students), 3)

    def test_override_default_operators(self):
        items = db.session.query(Student).all()
        qmod = FilterListModifier(self.filters)

        class Age2NameFilter(QueryFilter):
            
            def modify_column(self, column):
                return "name"

        qmod = FilterListModifier(
            self.filters, overrides=dict(age=[
                Age2NameFilter(operator="=", method_query=operator.eq)
            ])
        )

        students = qmod.apply(items, ["age=Anna"])

        self.assertEqual(len(students), 2)