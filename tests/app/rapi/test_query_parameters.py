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
from app.rapi.utils import *
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

@mock.patch(
    "app.rapi.utils.request", 
    args=dict(
        filter="name=JAGO;age=5", sort="-age,name", limit=10, offset=5,
        fields="name,age"
    )
)
class FlaskRequestParamsReaderTest(unittest.TestCase):

    def test_read_fiels_params(self, request):
        params_reader = FlaskRequestParamsReader()

        params = params_reader.get_fields_params()

        self.assertEqual(len(params), 2)
        self.assertEqual(params[0], "name")
        self.assertEqual(params[1], "age")
     

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