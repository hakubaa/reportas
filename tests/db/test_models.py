import unittest
import json

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref

from tests.app import AppTestCase
from app import db
from db.models import Company
from db.core import Model, VersionedModel


class TestVersioning(AppTestCase):

    class Address(VersionedModel):
        id = Column(Integer, primary_key=True)
        city = Column(String)
        street = Column(String)

    class Student(VersionedModel):
        id = Column(Integer, primary_key=True)
        age = Column(Integer)
        name = Column(String, nullable=False)

        address_id = Column(Integer, ForeignKey("address.id"))
        address = relationship("Address", backref=backref("students"))

    def test_for_saving_previous_data_in_db_when_updating_object(self):
        student = TestVersioning.Student(name="Python", age=17)
        db.session.add(student)
        db.session.commit()
        student.age += 1
        db.session.commit()

        history_cls = TestVersioning.Student.__history_mapper__.class_
        self.assertEqual(db.session.query(history_cls).count(), 1)

        student_prev = db.session.query(history_cls).one()
        self.assertEqual(student_prev.age, 17)

    def test_deleting_object_saves_previous_version_in_db(self):
        student = TestVersioning.Student(name="Python", age=17)
        db.session.add(student)
        db.session.commit()
        db.session.delete(student)
        db.session.commit()

        history_cls = TestVersioning.Student.__history_mapper__.class_
        self.assertEqual(db.session.query(history_cls).count(), 1)

        student_prev = db.session.query(history_cls).one()
        self.assertEqual(student_prev.name, "Python")   

    def test_change_of_relation_is_saved_in_history_table(self):
        address = TestVersioning.Address(city="Warsaw", street="Main Street")
        student = TestVersioning.Student(name="Jacob", age=18, address=address)
        db.session.add_all((address, student))
        db.session.commit()
        new_address = TestVersioning.Address(city="Praha", street="Golden Street")
        db.session.add(new_address)
        student.address = new_address
        db.session.commit()

        history_cls = TestVersioning.Student.__history_mapper__.class_
        self.assertEqual(db.session.query(history_cls).count(), 1)

        student_prev = db.session.query(history_cls).one()
        self.assertEqual(student_prev.address_id, address.id)   