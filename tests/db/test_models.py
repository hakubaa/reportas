import unittest
from unittest import mock
import json
from datetime import date

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref

from tests.app import AppTestCase
from app import db
from db.models import (
    Company, RecordType, RecordFormula, FormulaComponent, Record,
    FinancialStatementType
)
from db.core import Model, VersionedModel
import db.utils as utils
import db.tools as tools

#-------------------------------------------------------------------------------

def create_ftype(name="bls"):
    ftype = FinancialStatementType(name=name)
    db.session.add(ftype)
    db.session.commit()
    return ftype


def create_rtype(ftype, name="TOTAL_ASSETS", timeframe="pot"):
    total_assets = RecordType(name=name, ftype=ftype, timeframe=timeframe)
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


def create_rtypes(ftype, timeframe="pot"):
    if not ftype:
        ftype = create_ftype(name="bls")
    total_assets = RecordType(
        name="TOTAL_ASSETS", ftype=ftype, timeframe=timeframe
    )
    current_assets = RecordType(
        name="CURRENT_ASSETS", ftype=ftype, timeframe=timeframe
    )
    fixed_assets = RecordType(
        name="FIXED_ASSETS", ftype=ftype, timeframe=timeframe
    )
    db.session.add_all((total_assets, current_assets, fixed_assets))
    db.session.commit()    
    return total_assets, current_assets, fixed_assets


def create_db_formula(left, right):
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

    def test_add_component_creates_new_components(self):
        ta, ca, fa = create_rtypes(create_ftype("bls"))
        
        formula = RecordFormula(rtype=ta)
        formula.add_component(rtype=ca, sign=1)
        formula.add_component(rtype=fa, sign=1)
        db.session.commit()
        
        self.assertEqual(db.session.query(FormulaComponent).count(), 2)
        
    def test_add_component_accepts_predefined_components(self):
        ta, ca, fa = create_rtypes(create_ftype("bls"))
        comp_ca = FormulaComponent(rtype=ca, sign=1)
        comp_fa = FormulaComponent(rtype=fa, sign=1)
        db.session.add_all((comp_ca, comp_fa))
        
        formula = RecordFormula(rtype=ta)
        formula.add_component(comp_ca)
        formula.add_component(comp_fa)
        db.session.commit()
        
        self.assertCountEqual(formula.components, [comp_ca, comp_fa])
        
    def test_repr_enables_to_identify_formula(self):
        ta, ca, fa = create_rtypes(create_ftype("bls"))
        
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
        ta, ca, fa = create_rtypes(create_ftype("bls"))
        formula = create_db_formula(ta, ((1, ca), (1, fa)))
        
        new_formula = formula.transform(ca)
        db.session.add(new_formula)
        db.session.commit()
        
        self.assertNotEqual(formula.id, new_formula.id)
        
    def test_transform_raises_error_when_new_left_side_not_in_components(self):
        ftype = create_ftype(name="bls")
        ta, ca, fa = create_rtypes(ftype)
        eq = RecordType(name="EQUITY", ftype=ftype)
        db.session.add(eq)
        db.session.commit()
        formula = create_db_formula(ta, ((1, ca), (1, fa)))
        
        with self.assertRaises(Exception):
            formula.transform(eq)

    def test_transform_sets_proper_left_hand_side(self):
        ta, ca, fa = create_rtypes(create_ftype("bls"))
        formula = create_db_formula(ta, ((1, ca), (1, fa)))
        
        new_formula = formula.transform(ca)
        
        self.assertEqual(new_formula.lhs, ca)

    def test_transform_sets_proper_right_hand_side(self):
        ta, ca, fa = create_rtypes(create_ftype("bls"))
        formula = create_db_formula(ta, ((1, ca),))
        
        new_formula = formula.transform(ca)

        self.assertEqual(len(new_formula.rhs), 1)
        self.assertEqual(new_formula.rhs[0].rtype, ta)
        self.assertEqual(new_formula.rhs[0].sign, 1)

    def test_similar_formula_have_the_same_hash(self):
        ta, ca, fa = create_rtypes(create_ftype("bls"))
        
        formula1 = create_db_formula(ta, ((1, ca), (1, fa)))
        formula2 = create_db_formula(ta, ((1, ca), (1, fa)))

        self.assertEqual(hash(formula1), hash(formula2))

    def test_similar_formula_are_equal(self):
        ta, ca, fa = create_rtypes(create_ftype("bls"))
        
        formula1 = create_db_formula(ta, ((1, ca), (1, fa)))
        formula2 = create_db_formula(ta, ((1, ca), (1, fa)))

        self.assertEqual(formula1, formula2)


class RecordTest(AppTestCase):

    def setUp(self):
        super().setUp()
        self.ftype_bls = create_ftype(name="ics")
        self.rtype = create_rtype(ftype=self.ftype_bls, name="RECORD_RTYPE")
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
        self, fiscal_year_start_month, timerange, timestamp,
        rtype=None
    ):
        company = create_company(
             fiscal_year_start_month=fiscal_year_start_month
        )
        record = create_record(
            company=company, rtype=rtype or self.rtype, value=0,
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

    def test_project_pit_record_timestamp_on_fiscal_year_test01(self):
        ftype = create_ftype(name="bls")
        rtype = create_rtype(ftype, timeframe="pit")
        record = self.create_record_for_projection_test(
            fiscal_year_start_month=1, rtype=rtype,
            timerange=0,
            timestamp = date(2015, 6, 30)
        )
        self.assert_projection(record, 6, 6)

    def test_project_pit_record_timestamp_on_fiscal_year_test02(self):
        ftype = create_ftype(name="bls")
        rtype = create_rtype(ftype, timeframe="pit")
        record = self.create_record_for_projection_test(
            fiscal_year_start_month=7, rtype=rtype,
            timerange=0,
            timestamp = date(2015, 6, 30)
        )
        self.assert_projection(record, 12, 12)

    def test_project_pit_record_timestamp_on_fiscal_year_test03(self):
        ftype = create_ftype(name="bls")
        rtype = create_rtype(ftype, timeframe="pit")
        record = self.create_record_for_projection_test(
            fiscal_year_start_month=7, rtype=rtype,
            timerange=9,
            timestamp = date(2015, 7, 31)
        )
        self.assert_projection(record, 1, 1)

    def test_timerange_of_pit_records_is_always_set_to_zero(self):
        rtype = create_rtype(ftype=create_ftype(name="bls"), timeframe="pit")
        company = create_company()

        record = Record(
            company=company, rtype=rtype, timerange=12,
            timestamp=date(2015, 12, 31), value=10
        )
        db.session.add(record)
        db.session.commit()

        self.assertEqual(record.timerange, 0)

    def test_timerange_of_pit_records_cannot_be_change(self):
        rtype = create_rtype(ftype=create_ftype(name="bls"), timeframe="pit")
        company = create_company()

        record = Record(
            company=company, rtype=rtype, timerange=0,
            timestamp=date(2015, 12, 31), value=10
        )
        db.session.add(record)
        db.session.commit()

        record.timerange = 5
        db.session.commit()

        self.assertEqual(record.timerange, 0)

    def test_timerange_of_pot_records_can_take_any_number(self):
        rtype = create_rtype(ftype=create_ftype(name="bls"), timeframe="pot")
        company = create_company()

        record = Record(
            company=company, rtype=rtype, timerange=12,
            timestamp=date(2015, 12, 31), value=10
        )
        db.session.add(record)
        db.session.commit()

        self.assertEqual(record.timerange, 12)


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


    @mock.patch("db.models.Record.create_synthetic_records_for_company")
    def test_create_synthetic_records(self, csr_mock):
        csr_mock.return_value = list()
        
        company1 = create_company()
        company2 = create_company()
        ftype = create_ftype(name="bls")
        rtype = create_rtype(ftype)
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
        ftype = create_ftype(name="bls")
        rtype = create_rtype(ftype)
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
        
    def test_get_records_for_company_within_fiscal_year(self):
        company1 = create_company()
        company2 = create_company()
        ftype = create_ftype(name="ics")
        rtype = create_rtype(ftype)
        records = self.create_records([
            (company1, rtype, 12, date(2015, 12, 31), 0),
            (company1, rtype, 3, date(2015, 3, 31), 0),
            (company1, rtype, 12, date(2014, 12, 31), 0),
            (company2, rtype, 12, date(2015, 12, 31), 0)
        ]) 
        
        timerange = utils.TimeRange(
            start=date(2015, 1, 1), end=date(2015, 12, 31)
        )
        records_ = Record.get_records_for_company_within_fiscal_year(
            db.session, company1, timerange
        )

        self.assertEqual(len(records_), 2)
        self.assertCountEqual(records_, (records[0], records[1]))

    def test_get_records_for_company_within_fiscal_year_returns_only_genuine_records(self):
        company = create_company()
        rtype = create_rtype(create_ftype(name="ics"))
        record1 = Record(
            company=company, rtype=rtype, timerange=12, synthetic=False,
            timestamp=date(2015, 12, 31), value=10
        )
        record2 = Record(
            company=company, rtype=rtype, timerange=3, synthetic=True,
            timestamp=date(2015, 3, 31), value=20
        )
        db.session.add_all([record1, record2])
        db.session.commit()

        timerange = utils.TimeRange(
            start=date(2015, 1, 1), end=date(2015, 12, 31)
        )
        records = Record.get_records_for_company_within_fiscal_year(
            db.session, company, timerange
        )
        self.assertEqual(len(records), 1)
        self.assertCountEqual(records, (record1,))
        
    def test_csr_creates_new_records_pot(self):
        company = create_company()
        ftype = create_ftype(name="bls")
        ta, ca, fa = create_rtypes(ftype)
        formula = create_db_formula(ta, ((1, ca), (1, fa)))
        
        records = self.create_records([
            (company, ca, 12, date(2015, 12, 31), 40),
            (company, fa, 12, date(2015, 12, 31), 60),
        ]) 
        
        new_records = Record.create_synthetic_records_for_company_within_fiscal_year(
            db.session, company=company,
            fiscal_year=utils.FiscalYear(date(2015, 1, 1), date(2015, 12, 31)),
            base_records = [records[0]]
        )
        
        self.assertEqual(len(new_records), 1)
        self.assertEqual(new_records[0].rtype, ta)
        self.assertEqual(new_records[0].value, 100)
        self.assertEqual(new_records[0].timerange, 12)
        self.assertEqual(new_records[0].timestamp, date(2015, 12, 31))

    def test_csr_creates_new_records_pit_and_pot_mixed(self):
        company = create_company()
        ftype_bls = create_ftype(name="bls")
        ftype_ics = create_ftype(name="ics")

        ta = RecordType(name="TOTAL", ftype=ftype_ics, timeframe="pit")
        ca = RecordType(name="CURRENT", ftype=ftype_ics, timeframe="pit")
        fa = RecordType(name="FIXED", ftype=ftype_ics, timeframe="pit")       

        revenues = RecordType(name="REVENUES", ftype=ftype_ics, timeframe="pot")
        costs = RecordType(name="COSTS", ftype=ftype_ics, timeframe="pot")
        profit = RecordType(name="PROFIT", ftype=ftype_ics, timeframe="pot")

        db.session.add_all((ta, ca, fa, revenues, costs, profit))
        db.session.commit()    

        formula_ta = create_db_formula(ta, ((1, ca), (1, fa)))
        formula_profit = create_db_formula(profit, ((1, revenues), (-1, costs)))

        records = self.create_records([
            (company, ca, 0, date(2015, 12, 31), 40),
            (company, fa, 0, date(2015, 12, 31), 60),
            (company, revenues, 12, date(2015, 12, 31), 100),
            (company, costs, 12, date(2015, 12, 31), 80),
        ]) 

        new_records = Record.create_synthetic_records_for_company_within_fiscal_year(
            db.session, company=company,
            fiscal_year=utils.FiscalYear(date(2015, 1, 1), date(2015, 12, 31)),
            base_records = records
        )

        self.assertEqual(len(new_records), 2)

        record_total = next(filter(lambda x: x.rtype == ta, new_records))
        record_profit = next(filter(lambda x: x.rtype == profit, new_records))

        self.assertEqual(record_total.value, 100)
        self.assertEqual(record_total.timerange, 0)
        self.assertEqual(record_total.timestamp, date(2015, 12, 31))

        self.assertEqual(record_profit.value, 20)
        self.assertEqual(record_profit.timerange, 12)
        self.assertEqual(record_profit.timestamp, date(2015, 12, 31))

    def test_csr_creates_new_records_pit(self):
        company = create_company()
        ftype = create_ftype(name="bls")
        ta, ca, fa = create_rtypes(ftype, timeframe="pit")
        formula = create_db_formula(ta, ((1, ca), (1, fa)))
        
        records = self.create_records([
            (company, ca, 12, date(2015, 12, 31), 40),
            (company, fa, 12, date(2015, 12, 31), 60),
        ]) 
        
        new_records = Record.create_synthetic_records_for_company_within_fiscal_year(
            db.session, company=company,
            fiscal_year=utils.FiscalYear(date(2015, 1, 1), date(2015, 12, 31)),
            base_records = [records[0]]
        )

        self.assertEqual(len(new_records), 1)
        self.assertEqual(new_records[0].rtype, ta)
        self.assertEqual(new_records[0].value, 100)
        self.assertEqual(new_records[0].timerange, 0)
        self.assertEqual(new_records[0].timestamp, date(2015, 12, 31))

    def test_csr_creates_new_records_with_timerange(self):
        company = create_company()
        ftype = create_ftype(name="test")
        ta, ca, fa = create_rtypes(ftype)
        
        records = self.create_records([
            (company, ta, 3, date(2015, 3, 31), 40),
            (company, ta, 6, date(2015, 6, 30), 60),
        ])        
        
        new_records = Record.create_synthetic_records_for_company_within_fiscal_year(
            db.session, company=company,
            fiscal_year=utils.FiscalYear(date(2015, 1, 1), date(2015, 12, 31)),
            base_records = [records[0]]
        )

        self.assertEqual(len(new_records), 1)
        self.assertEqual(new_records[0].rtype, ta)
        self.assertEqual(new_records[0].value, 20)
        self.assertEqual(new_records[0].timerange, 3)
        self.assertEqual(new_records[0].timestamp, date(2015, 6, 30))

    def test_csr_updates_already_existing_synthetic_records(self):
        company = create_company()
        ta, ca, fa = create_rtypes(create_ftype(name="cfs"), timeframe="pot")
        formula = create_db_formula(ta, ((1, ca), (1, fa)))
        
        records = self.create_records([
            (company, ca, 12, date(2015, 12, 31), 120), # updated from 40 to 120
            (company, fa, 12, date(2015, 12, 31), 60),
            (company, ta, 12, date(2015, 12, 31), 100) # previous synthetic record
        ]) 
        self.assertEqual(records[2].rtype, ta)
        records[2].synthetic = True
        db.session.commit()

        new_records = Record.create_synthetic_records_for_company_within_fiscal_year(
            db.session, company=company,
            fiscal_year=utils.FiscalYear(date(2015, 1, 1), date(2015, 12, 31)),
            base_records = [records[0]]
        ) 

        self.assertEqual(len(new_records), 1)
        self.assertEqual(new_records[0], records[2])
        self.assertEqual(new_records[0].value, 180)


class FinancialStatementTypeTest(AppTestCase):

    def test_insert_default_ftypes(self):
        FinancialStatementType.insert_defaults(db.session)
        db.session.commit()

        self.assertEqual(db.session.query(FinancialStatementType).count(), 3)
        db.session.query(FinancialStatementType).filter_by(name="bls").one()
        db.session.query(FinancialStatementType).filter_by(name="ics").one()
        db.session.query(FinancialStatementType).filter_by(name="cfs").one()