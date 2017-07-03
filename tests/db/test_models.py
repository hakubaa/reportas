import unittest
import json

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref

from tests.app import AppTestCase
from app import db
from db.models import Company
from db.core import Model, VersionedModel



################################################################################
# CREATE MODELS FOR TESTS
################################################################################

class Student(VersionedModel):
    id = Column(Integer, primary_key=True)
    age = Column(Integer)
    name = Column(String, nullable=False)


class Subject(VersionedModel):
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    student_id = Column(Integer, ForeignKey("student.id"))
    student = relationship("Student", backref=backref("subjects"))


################################################################################


class TestVersioning(AppTestCase):

    def test_test(self):
        student = Student(name="Python", age=18)
        db.session.add(student)
        subject = Subject(name="Math")
        db.session.add(subject)
        student.subject = subject
        db.session.commit()
        import pdb; pdb.set_trace()

