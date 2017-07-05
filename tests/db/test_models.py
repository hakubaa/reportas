import unittest
import json

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref

from tests.app import AppTestCase
from app import db
from db.models import Company, RecordType, RecordFormula, FormulaComponent
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


class RecordFormulaTest(AppTestCase):
    
    def create_rtypes(self):
        total_assets = RecordType(name="TOTAL_ASSETS", statement="bls")
        current_assets = RecordType(name="CURRENT_ASSETS", statement="bls")
        fixed_assets = RecordType(name="FIXED_ASSETS", statement="bls")
        db.session.add_all((total_assets, current_assets, fixed_assets))
        db.session.commit()    
        return total_assets, current_assets, fixed_assets
    
    def test_add_component_creates_new_components(self):
        ta, ca, fa = self.create_rtypes()
        
        formula = RecordFormula(rtype=ta)
        formula.add_component(rtype=ca, sign=1)
        formula.add_component(rtype=fa, sign=1)
        db.session.commit()
        
        self.assertEqual(db.session.query(FormulaComponent).count(), 2)
        
    def test_add_component_accepts_predefined_components(self):
        ta, ca, fa = self.create_rtypes()
        comp_ca = FormulaComponent(rtype=ca, sign=1)
        comp_fa = FormulaComponent(rtype=fa, sign=1)
        db.session.add_all((comp_ca, comp_fa))
        
        formula = RecordFormula(rtype=ta)
        formula.add_component(comp_ca)
        formula.add_component(comp_fa)
        db.session.commit()
        
        self.assertCountEqual(formula.components, [comp_ca, comp_fa])
        
    def test_repr_enables_to_identify_formula(self):
        ta, ca, fa = self.create_rtypes()
        
        formula = RecordFormula(rtype=ta)
        formula.add_component(rtype=ca, sign=1)
        formula.add_component(rtype=fa, sign=-1)
        db.session.commit()
        
        formula_repr = repr(formula)
        self.assertEqual(
            formula_repr,
            "RecordFormula<TOTAL_ASSETS, CURRENT_ASSETS - FIXED_ASSETS>"
        )