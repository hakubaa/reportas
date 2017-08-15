import unittest
from unittest.mock import patch
import json

from sqlalchemy import Column, Integer, String
from marshmallow_sqlalchemy import ModelSchema

from tests.db import DbTestCase
from db.factory import DBRecordFactory
from db.core import Model

################################################################################
# CREATE MODELS FOR TESTS
################################################################################

class Student(Model):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    age = Column(Integer)
    name = Column(String, nullable=False)
    
class StudentSchema(ModelSchema):
    class Meta:
        model = Student

################################################################################

class InstanceFactoryTest(DbTestCase):

    def create_student(self, name="Python", age=17):
        student = Student(name=name, age=age)
        self.db.session.add(student)
        self.db.session.commit()
        return student

    def test_register_model_saves_new_entry_in_inner_dict(self):
        factory = DBRecordFactory(session=self.db.session)
        
        factory.register_model(Student, StudentSchema)
        
        self.assertIn(Student, factory.models)
        self.assertEqual(StudentSchema, factory.models[Student])
        
    def test_create_record_with_create_method(self):
        factory = DBRecordFactory(session=self.db.session)
        factory.register_model(Student, StudentSchema)
        
        factory.create(Student, name="Python", age=17)
        self.db.session.commit()
        
        student = self.db.session.query(Student).one()
        self.assertEqual(student.name, "Python")
        self.assertEqual(student.age, 17)
        
    def test_create_returns_errors_when_sth_goes_wrong(self):
        factory = DBRecordFactory(session=self.db.session)
        factory.register_model(Student, StudentSchema)
        
        obj, errors = factory.create(Student, username="Python", age=17)
        
        self.assertIsNone(self.db.session.query(Student).first())
        self.assertIn("name", errors)
        
    def test_create_record_raises_error_when_no_schema(self):
        factory = DBRecordFactory(session=self.db.session)
        
        with self.assertRaises(RuntimeError):
            factory.create(Student, name="Python", age=17)
        
    def test_update_record_raises_error_when_no_schema(self):
        factory = DBRecordFactory(session=self.db.session)
        student = self.create_student()
        
        with self.assertRaises(RuntimeError):
            factory.update(student, name="Python", age=17)
            
    def test_update_records_updates_record_with_proper_data(self):
        factory = DBRecordFactory(session=self.db.session)
        factory.register_model(Student, StudentSchema)
        student = self.create_student()
        
        factory.update(student, name="Reportas", age=1)
        self.db.session.commit()
        
        student = self.db.session.query(Student).first()
        self.assertEqual(student.name, "Reportas")
        self.assertEqual(student.age, 1)

    def test_for_registering_model_with_decorator(self):
        factory = DBRecordFactory(session=self.db.session)

        @factory.register_schema()
        class StudentSchema(ModelSchema):
            class Meta:
                model = Student

        self.assertEqual(factory.get_schema(Student), StudentSchema)

    def test_get_schema_accepts_class_as_string(self):
        factory = DBRecordFactory(session=self.db.session)
        factory.register_model(Student, StudentSchema)
        
        schema = factory.get_schema("Student")
        
        self.assertEqual(schema, StudentSchema)

    def test_updating_instance_without_any_data_does_not_raise_erros(self):
        factory = DBRecordFactory(session=self.db.session)
        factory.register_model(Student, StudentSchema)
        student = self.create_student()
        
        obj, errors = factory.update(student)

        self.assertFalse(errors)
        self.assertEqual(obj, student)

    def test_id_in_data_is_ignored_when_updating(self):
        factory = DBRecordFactory(session=self.db.session)
        factory.register_model(Student, StudentSchema)
        student = self.create_student()
        
        obj, errors = factory.update(student, id=student.id)

        self.assertFalse(errors)
        self.assertEqual(obj, student)