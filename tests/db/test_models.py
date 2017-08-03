import unittest
from unittest import mock
import json
from datetime import date

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref

from tests.app import AppTestCase
from app import db
from db.models import (
    Company, RecordType, RecordFormula, FormulaComponent, Record
)
from db.core import Model, VersionedModel
import db.utils as utils
import db.tools as tools

#-------------------------------------------------------------------------------

def create_rtype(name="TOTAL_ASSETS", statement="bls"):
    total_assets = RecordType(name=name, statement=statement)
    db.session.add(total_assets)
    db.session.commit()    
    return total_assets


def counter_decorator(func):
    func.counter = 0
    return func
    

@counter_decorator
def create_company(name=None, isin=None, fiscal_year_start_month = 1):
    if not name:
        name = "TEST#%s" % create_company.counter
    if not isin:
        isin = "#TEST#%s" % create_company.counter
    create_company.counter += 1
    company = Company(
        name=name, isin=isin, fiscal_year_start_month=fiscal_year_start_month
    )
    db.session.add(company)
    db.session.commit()
    return company


def create_record(**kwargs):
    record = Record(**kwargs)
    db.session.add(record)
    db.session.commit()
    return record


def create_rtypes():
    total_assets = RecordType(name="TOTAL_ASSETS", statement="bls")
    current_assets = RecordType(name="CURRENT_ASSETS", statement="bls")
    fixed_assets = RecordType(name="FIXED_ASSETS", statement="bls")
    db.session.add_all((total_assets, current_assets, fixed_assets))
    db.session.commit()    
    return total_assets, current_assets, fixed_assets


def create_formula(left, right):
    formula = RecordFormula(rtype=left)
    db.session.add(formula)
    for item in right:
        formula.add_component(rtype=item[1], sign=item[0])
    db.session.commit()
    return formula

#-------------------------------------------------------------------------------

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

    def create_formula(self, left, right):
        formula = RecordFormula(rtype=left)
        db.session.add(formula)
        for item in right:
            formula.add_component(rtype=item[1], sign=item[0])
        db.session.commit()
        return formula

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

    def test_transform_creates_and_returns_new_formula(self):
        ta, ca, fa = self.create_rtypes()
        formula = self.create_formula(ta, ((1, ca), (1, fa)))
        
        new_formula = formula.transform(ca)
        db.session.add(new_formula)
        db.session.commit()
        
        self.assertNotEqual(formula.id, new_formula.id)
        
    def test_transform_raises_error_when_new_left_side_not_in_components(self):
        ta, ca, fa = self.create_rtypes()
        eq = RecordType(name="EQUITY", statement="bls")
        db.session.add(eq)
        db.session.commit()
        formula = self.create_formula(ta, ((1, ca), (1, fa)))
        
        with self.assertRaises(Exception):
            formula.transform(eq)

    def test_transform_sets_proper_left_hand_side(self):
        ta, ca, fa = self.create_rtypes()
        formula = self.create_formula(ta, ((1, ca), (1, fa)))
        
        new_formula = formula.transform(ca)
        
        self.assertEqual(new_formula.lhs, ca)

    def test_transform_sets_proper_right_hand_side(self):
        ta, ca, fa = self.create_rtypes()
        formula = self.create_formula(ta, ((1, ca),))
        
        new_formula = formula.transform(ca)

        self.assertEqual(len(new_formula.rhs), 1)
        self.assertEqual(new_formula.rhs[0].rtype, ta)
        self.assertEqual(new_formula.rhs[0].sign, 1)

    def test_similar_formula_have_the_same_hash(self):
        ta, ca, fa = self.create_rtypes()
        
        formula1 = self.create_formula(ta, ((1, ca), (1, fa)))
        formula2 = self.create_formula(ta, ((1, ca), (1, fa)))

        self.assertEqual(hash(formula1), hash(formula2))

    def test_similar_formula_are_equal(self):
        ta, ca, fa = self.create_rtypes()
        
        formula1 = self.create_formula(ta, ((1, ca), (1, fa)))
        formula2 = self.create_formula(ta, ((1, ca), (1, fa)))

        self.assertEqual(formula1, formula2)


class RecordTest(AppTestCase):

    def setUp(self):
        super().setUp()
        self.rtype = create_rtype()
        self.company = create_company(name="RecordTest", isin="#RecordTest")

    def create_record(
        self, timerange, timestamp, value=100, rtype=None, company=None
    ):
        record = Record(
            rtype=rtype or self.rtype, company=company or self.company, 
            timerange=timerange, timestamp=timestamp, value=value
        )
        db.session.add(record)
        db.session.commit()
        return record     


    def assert_fiscal_year(self, record, fy_start, fy_end):
        fy_start_, fy_end_ = record.determine_fiscal_year()
        self.assertEqual(fy_start, fy_start_)
        self.assertEqual(fy_end, fy_end_)

    def test_determine_fiscal_year_test01(self):
        company = create_company(fiscal_year_start_month=1)
        record = self.create_record(
            timerange = 12,
            timestamp = date(2015, 12, 31),
            company = company
        )

        self.assert_fiscal_year(
            record,
            fy_start=date(2015, 1, 1), fy_end=date(2015, 12, 31)
        )

    def test_determine_fiscal_year_test02(self):
        company = create_company(fiscal_year_start_month=7)
        record = self.create_record(
            timerange = 3,
            timestamp = date(2015, 3, 31),
            company = company
        )

        self.assert_fiscal_year(
            record,
            fy_start=date(2014, 7, 1), fy_end=date(2015, 6, 30)
        )

    def test_determine_fiscal_year_test03(self):
        company = create_company(fiscal_year_start_month=4)
        record = self.create_record(
            timerange = 3,
            timestamp = date(2015, 3, 31),
            company = company
        )

        self.assert_fiscal_year(
            record,
            fy_start=date(2014, 4, 1), fy_end=date(2015, 3, 31)
        )

    def test_determine_fiscal_year_test04(self):
        company = create_company(fiscal_year_start_month=4)
        record = self.create_record(
            timerange = 2,
            timestamp = date(2015, 5, 31),
            company = company
        )

        self.assert_fiscal_year(
            record,
            fy_start=date(2015, 4, 1), fy_end=date(2016, 3, 31)
        )

    def test_determine_fiscal_year_test05(self):
        company = create_company(fiscal_year_start_month=6)
        record = self.create_record(
            timerange = 12,
            timestamp = date(2015, 5, 31),
            company = company
        )

        self.assert_fiscal_year(
            record,
            fy_start=date(2014, 6, 1), fy_end=date(2015, 5, 31)
        )

    def test_determine_fiscal_year_test06(self):
        company = create_company(fiscal_year_start_month=1)
        record = self.create_record(
            timerange = 1,
            timestamp = date(2015, 1, 31),
            company = company
        )

        self.assert_fiscal_year(
            record,
            fy_start=date(2015, 1, 1), fy_end=date(2015, 12, 31)
        )

    def test_timestamp_start_returns_proper_value_test01(self):
        record = self.create_record(
            timerange = 12,
            timestamp = date(2015, 12, 31)
        )

        self.assertEqual(record.timestamp_start, date(2015, 1, 1))

    def test_timestamp_start_returns_proper_value_test02(self):
        record = self.create_record(
            timerange = 3,
            timestamp = date(2015, 12, 31)
        )

        self.assertEqual(record.timestamp_start, date(2015, 10, 1))

    def test_timestamp_start_returns_proper_value_test03(self):
        record = self.create_record(
            timerange = 3,
            timestamp = date(2015, 6, 30)
        )

        self.assertEqual(record.timestamp_start, date(2015, 4, 1))

    @unittest.skip # require postgresql
    def test_query_records_by_timestamp_start(self):
        self.create_record(timerange = 3, timestamp = date(2015, 12, 31)) 
        self.create_record(timerange = 6, timestamp = date(2015, 12, 31)) 

        records = db.session.query(Record).\
                  filter(Record.timestamp_start >= date(2015, 10, 1)).all()

        self.assertEqual(len(records), 1)

    def create_record_for_projection_test(
        self, fiscal_year_start_month, timerange, timestamp
    ):
        company = create_company(
             fiscal_year_start_month=fiscal_year_start_month
        )
        record = create_record(
            company=company, rtype=self.rtype, value=0,
            timerange=timerange, timestamp=timestamp
        )     
        return record  
    
    def assert_projection(self, record, start, end):
        timerange_start, timerange_end = \
            record.project_onto_fiscal_year()
        
        self.assertEqual(timerange_start, start)
        self.assertEqual(timerange_end, end)  
        
    def test_project_timestamps_on_fiscal_year_test01(self):
        record = self.create_record_for_projection_test(
            fiscal_year_start_month = 1,
            timerange = 12,
            timestamp = date(2015, 12, 31)
        )
        
        self.assert_projection(record, 1, 12)
        
    def test_project_timestamps_on_fiscal_year_test02(self):
        record = self.create_record_for_projection_test(
            fiscal_year_start_month = 1,
            timerange = 3,
            timestamp = date(2015, 6, 30)
        )
        
        self.assert_projection(record, 4, 6)
        
    def test_project_timestamps_on_fiscal_year_test03(self):
        record = self.create_record_for_projection_test(
            fiscal_year_start_month = 7,
            timerange = 12,
            timestamp = date(2015, 6, 30)
        )
        
        self.assert_projection(record, 1, 12)
        
    def test_project_timestamps_on_fiscal_year_test04(self):
        record = self.create_record_for_projection_test(
            fiscal_year_start_month = 9,
            timerange = 3,
            timestamp = date(2015, 3, 31)
        )

        self.assert_projection(record, 5, 7)


class SyntheticReccordsTest(AppTestCase):
    
    def create_records(self, data):
        records = list()
        for item in data:
            records.append(
                create_record(
                    company=item[0], rtype=item[1], timerange=item[2], 
                    timestamp=item[3], value=item[4]
                )
            )
        return records

    def test_group_records_by_company(self):
        company1 = create_company()
        company2 = create_company()
        rtype = create_rtype()
        records = self.create_records([
            (company1, rtype, 12, date(2015, 12, 31), 0),
            (company1, rtype, 12, date(2014, 12, 31), 0),
            (company2, rtype, 12, date(2015, 12, 31), 0)
        ])        
        
        records_map = utils.group_objects(records, key=lambda item: item.company)
        
        self.assertIsInstance(records_map, dict)
        self.assertEqual(len(records_map), 2)
        self.assertCountEqual(records_map.keys(), (company1, company2))
        self.assertEqual(len(records_map[company1]), 2)
        self.assertEqual(len(records_map[company2]), 1)
        
    def test_group_records_by_fiscal_year(self):
        company = create_company()  
        rtype = create_rtype()
        records = self.create_records([
            (company, rtype, 12, date(2015, 12, 31), 0),
            (company, rtype, 12, date(2014, 12, 31), 0),
            (company, rtype, 3, date(2015, 3, 31), 0)
        ])     
        
        records_map = utils.group_objects(
            records, key=lambda item: item.determine_fiscal_year()
        )
        
        fy_1 = (date(2015, 1, 1), date(2015, 12, 31))
        fy_2 = (date(2014, 1, 1), date(2014, 12, 31))
        
        self.assertIsInstance(records_map, dict)
        self.assertEqual(len(records_map), 2)
        self.assertCountEqual(records_map.keys(), (fy_1, fy_2))
        self.assertEqual(len(records_map[fy_1]), 2)
        self.assertEqual(len(records_map[fy_2]), 1)        
        
    def test_concatenate_lists(self):
        test_list1 = [1, 2, 3]
        test_list2 = [4, 5, 6]
        test_list3 = [7, 8, 9]
        
        full_list = utils.concatenate_lists((test_list1, test_list2, test_list3))
        
        self.assertEqual(len(full_list), 9)
        self.assertCountEqual(full_list, range(1, 10))
        
    @mock.patch("db.models.Record.create_synthetic_records_for_company")
    def test_create_synthetic_records(self, csr_mock):
        csr_mock.return_value = list()
        
        company1 = create_company()
        company2 = create_company()
        rtype = create_rtype()
        records = self.create_records([
            (company1, rtype, 12, date(2015, 12, 31), 0),
            (company1, rtype, 12, date(2014, 12, 31), 0),
            # (company2, rtype, 12, date(2015, 12, 31), 0)
        ])    
        
        synrecs = Record.create_synthetic_records(db.session, records)
        
        self.assertEqual(csr_mock.call_count, 1)
        
        call_1st_args = csr_mock.call_args_list[0][0]
        self.assertEqual(call_1st_args[1], company1)
        self.assertCountEqual(call_1st_args[2], (records[0], records[1]))
        
        # call_2nd_args = csr_mock.call_args_list[1][0]
        # self.assertEqual(call_2nd_args[1], company2)
        # self.assertCountEqual(call_2nd_args[2], (records[2],))
        
    @mock.patch("db.models.Record.create_synthetic_records_for_company_within_fiscal_year")
    def test_create_synthetic_records_for_company(self, csr_mock):
        csr_mock.return_value = list()
        
        company = create_company()
        rtype = create_rtype()
        records = self.create_records([
            (company, rtype, 12, date(2015, 12, 31), 0),
            # (company, rtype, 12, date(2014, 12, 31), 0),
        ])    
        
        fy_1 = records[0].determine_fiscal_year()
        # fy_2 = records[1].determine_fiscal_year()
        
        synrecs = Record.create_synthetic_records_for_company(
            db.session, company, records
        )
        
        self.assertEqual(csr_mock.call_count, 1)

        call_1st_args = csr_mock.call_args_list[0][0]
        self.assertEqual(call_1st_args[2], fy_1)
        self.assertCountEqual(call_1st_args[3], (records[0],))
        
        # call_2nd_args = csr_mock.call_args_list[1][0]
        # self.assertEqual(call_2nd_args[2], (fy_1, fy_2))
        # self.assertCountEqual(call_2nd_args[3], (records[1],))     
        
    # @unittest.skip # require postgresql
    def test_get_records_for_company_within_fiscal_year(self):
        company1 = create_company()
        company2 = create_company()
        rtype = create_rtype()
        records = self.create_records([
            (company1, rtype, 12, date(2015, 12, 31), 0),
            (company1, rtype, 3, date(2015, 3, 31), 0),
            (company1, rtype, 12, date(2014, 12, 31), 0),
            (company2, rtype, 12, date(2015, 12, 31), 0)
        ]) 
        
        timerange = utils.TimeRange(
            start=date(2015, 1, 1), end=date(2015, 12, 31)
        )
        records_ = tools.get_records_for_company_within_fiscal_year(
            db.session, company1, timerange
        )

        self.assertEqual(len(records_), 2)
        self.assertCountEqual(records_, (records[0], records[1]))
        
        
    def test_represent_records_as_matrix(self):
        company = create_company()
        rtype1 = create_rtype(name="NET_PROFIT")
        rtype2 = create_rtype(name="REVENUE")
        records = self.create_records([
            (company, rtype1, 3, date(2015, 3, 31), 1),
            (company, rtype1, 6, date(2015, 6, 30), 2),
            (company, rtype2, 9, date(2015, 9, 30), 3),
            (company, rtype2, 12, date(2015, 12, 31), 4)
        ])    
        
        recmat = tools.represent_records_as_matrix(records)

        self.assertEqual(len(recmat), 2)
        self.assertCountEqual(recmat.keys(), (rtype1, rtype2))
        self.assertEqual(recmat[rtype1][utils.TimeRange(1, 3)], 1)
        self.assertEqual(recmat[rtype1][utils.TimeRange(1, 6)], 2)
        self.assertEqual(recmat[rtype2][utils.TimeRange(1, 9)], 3)
        self.assertEqual(recmat[rtype2][utils.TimeRange(1, 12)], 4)


class UtilsFormulaTest(AppTestCase):

    def test_convert_db_formula(self):
        ta, ca, fa = create_rtypes()
        db_formula = create_formula(ta, ((1, ca), (1, fa)))

        formula = utils.convert_db_formula(db_formula)

        self.assertIsInstance(formula, utils.Formula)
        self.assertEqual(formula.lhs.rtype, ta)
        self.assertEqual(len(formula.rhs), 2)

    def test_extend_formula_with_timerange(self):
        ta, ca, fa = create_rtypes()
        db_formula = create_formula(ta, ((1, ca), (1, fa)))

        formula = utils.convert_db_formula(db_formula)
        formula = formula.extend_with_timerange(utils.TimeRange(1, 3))

        self.assertIsInstance(formula.lhs, utils.Formula.TimeRangeComponent)
        self.assertTrue(all(
            map(lambda item: item.timerange == utils.TimeRange(1, 3), 
                formula.rhs))
        )

    def test_calculate_formula(self):
        ta, ca, fa = create_rtypes()
        db_formula = create_formula(ta, ((1, ca), (1, fa)))

        data = {
            ta: { utils.TimeRange(1, 3): 10 },
            ca: { utils.TimeRange(1, 3): 5 },
            fa: { utils.TimeRange(1, 3): 5 }
        }

        formula = utils.convert_db_formula(db_formula)
        formula = formula.extend_with_timerange(utils.TimeRange(1, 3))

        self.assertEqual(formula.calculate(data), 10)

    def test_is_calculable_returns_true_when_all_records_available(self):
        ta, ca, fa = create_rtypes()
        db_formula = create_formula(ta, ((1, ca), (1, fa)))

        data = {
            ta: { utils.TimeRange(1, 3): 10 },
            ca: { utils.TimeRange(1, 3): 5 },
            fa: { utils.TimeRange(1, 3): 5 }
        }

        formula = utils.convert_db_formula(db_formula)
        formula = formula.extend_with_timerange(utils.TimeRange(1, 3))

        self.assertTrue(formula.is_calculable(data))        

    def test_is_calculable_returns_false_when_not_all_records_available(self):
        ta, ca, fa = create_rtypes()
        db_formula = create_formula(ta, ((1, ca), (1, fa)))

        data = {
            ta: { utils.TimeRange(1, 3): 10 },
            fa: { utils.TimeRange(1, 3): 5 }
        }

        formula = utils.convert_db_formula(db_formula)
        formula = formula.extend_with_timerange(utils.TimeRange(1, 3))

        self.assertFalse(formula.is_calculable(data))        

    def test_timerange_formula(self):
        ta, ca, fa = create_rtypes()

        data = {
            ta: { 
                utils.TimeRange(1, 6): 10, 
                utils.TimeRange(1, 3): 5,
                utils.TimeRange(4, 6): 5
            }
        }

        formula = utils.create_timerange_formula(
            ta, lhs_spec=(utils.TimeRange(1, 6), 0),
            rhs_spec=[(utils.TimeRange(1, 3), 1), (utils.TimeRange(4, 6), 1)]
        )

        self.assertTrue(formula.is_calculable(data))
        self.assertEqual(formula.calculate(data), 10)

    def test_similar_formula_have_the_same_hash(self):
        ta, ca, fa = create_rtypes()
        db_formula = create_formula(ta, ((1, ca), (1, fa)))

        data = {
            ta: { utils.TimeRange(1, 3): 10 },
            ca: { utils.TimeRange(1, 3): 5 },
            fa: { utils.TimeRange(1, 3): 5 }
        }

        formula1 = utils.convert_db_formula(db_formula)
        formula2 = utils.convert_db_formula(db_formula)

        self.assertEqual(hash(formula1), hash(formula2))

    def test_similar_formula_are_equal(self):
        ta, ca, fa = create_rtypes()
        db_formula = create_formula(ta, ((1, ca), (1, fa)))

        data = {
            ta: { utils.TimeRange(1, 3): 10 },
            ca: { utils.TimeRange(1, 3): 5 },
            fa: { utils.TimeRange(1, 3): 5 }
        }

        formula1 = utils.convert_db_formula(db_formula)
        formula2 = utils.convert_db_formula(db_formula)

        self.assertEqual(formula1, formula2)