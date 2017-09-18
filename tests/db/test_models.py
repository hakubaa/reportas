import unittest
from unittest import mock
import json
from datetime import date

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref

from tests.db import DbTestCase
from tests.db.utils import *

from db.models import (
    Company, RecordType, RecordFormula, FormulaComponent, Record,
    FinancialStatement, FinancialStatementLayout, RTypeFSchemaAssoc,
    FinancialStatementLayoutRepr, FinancialStatementLayout
)
from db.core import Model, VersionedModel
import db.utils as utils
import db.tools as tools


@unittest.skip
class TestVersioning(DbTestCase):

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
        self.db.session.add(student)
        self.db.session.commit()
        student.age += 1
        self.db.session.commit()

        history_cls = TestVersioning.Student.__history_mapper__.class_
        self.assertEqual(self.db.session.query(history_cls).count(), 1)

        student_prev = self.db.session.query(history_cls).one()
        self.assertEqual(student_prev.age, 17)

    def test_deleting_object_saves_previous_version_in_db(self):
        student = TestVersioning.Student(name="Python", age=17)
        self.db.session.add(student)
        self.db.session.commit()
        self.db.session.delete(student)
        self.db.session.commit()

        history_cls = TestVersioning.Student.__history_mapper__.class_
        self.assertEqual(self.db.session.query(history_cls).count(), 1)

        student_prev = self.db.session.query(history_cls).one()
        self.assertEqual(student_prev.name, "Python")   

    def test_change_of_relation_is_saved_in_history_table(self):
        address = TestVersioning.Address(city="Warsaw", street="Main Street")
        student = TestVersioning.Student(name="Jacob", age=18, address=address)
        self.db.session.add_all((address, student))
        self.db.session.commit()
        new_address = TestVersioning.Address(city="Praha", street="Golden Street")
        self.db.session.add(new_address)
        student.address = new_address
        self.db.session.commit()

        history_cls = TestVersioning.Student.__history_mapper__.class_
        self.assertEqual(self.db.session.query(history_cls).count(), 1)

        student_prev = self.db.session.query(history_cls).one()
        self.assertEqual(student_prev.address_id, address.id)


class RecordFormulaTest(DbTestCase):

    def test_add_component_creates_new_components(self):
        ta, ca, fa = create_rtypes(
            self.db.session, create_ftype(self.db.session, "bls")
        )
        formula = RecordFormula(rtype=ta)
        formula.add_component(rtype=ca, sign=1)
        formula.add_component(rtype=fa, sign=1)
        self.db.session.commit()
        
        self.assertEqual(self.db.session.query(FormulaComponent).count(), 2)
        
    def test_add_component_accepts_predefined_components(self):
        ta, ca, fa = create_rtypes(
            self.db.session, create_ftype(self.db.session, "bls")
        )
        comp_ca = FormulaComponent(rtype=ca, sign=1)
        comp_fa = FormulaComponent(rtype=fa, sign=1)
        self.db.session.add_all((comp_ca, comp_fa))
        
        formula = RecordFormula(rtype=ta)
        formula.add_component(comp_ca)
        formula.add_component(comp_fa)
        self.db.session.commit()
        
        self.assertCountEqual(formula.components, [comp_ca, comp_fa])
        
    def test_repr_enables_to_identify_formula(self):
        ta, ca, fa = create_rtypes(
            self.db.session, create_ftype(self.db.session, "bls")
        )
        
        formula = RecordFormula(rtype=ta)
        formula.add_component(rtype=ca, sign=1)
        formula.add_component(rtype=fa, sign=-1)
        self.db.session.commit()
        
        formula_repr = repr(formula)
        self.assertEqual(
            formula_repr,
            "RecordFormula<TOTAL_ASSETS, CURRENT_ASSETS - FIXED_ASSETS>"
        )

    def test_transform_creates_and_returns_new_formula(self):
        ta, ca, fa = create_rtypes(
            self.db.session, create_ftype(self.db.session, "bls")
        )
        formula = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))
        
        new_formula = formula.transform(ca)
        self.db.session.add(new_formula)
        self.db.session.commit()
        
        self.assertNotEqual(formula.id, new_formula.id)
        
    def test_transform_raises_error_when_new_left_side_not_in_components(self):
        ftype = create_ftype(self.db.session, name="bls")
        ta, ca, fa = create_rtypes(self.db.session, ftype)
        eq = RecordType(name="EQUITY", ftype=ftype, timeframe=RecordType.PIT)
        self.db.session.add(eq)
        self.db.session.commit()
        formula = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))
        
        with self.assertRaises(Exception):
            formula.transform(eq)

    def test_transform_sets_proper_left_hand_side(self):
        ta, ca, fa = create_rtypes(
            self.db.session, create_ftype(self.db.session, "bls")
        )
        formula = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))
        
        new_formula = formula.transform(ca)
        
        self.assertEqual(new_formula.lhs, ca)

    def test_transform_sets_proper_right_hand_side(self):
        ta, ca, fa = create_rtypes(
            self.db.session, create_ftype(self.db.session, "bls")
        )
        formula = create_db_formula(self.db.session, ta, ((1, ca),))
        
        new_formula = formula.transform(ca)

        self.assertEqual(len(new_formula.rhs), 1)
        self.assertEqual(new_formula.rhs[0].rtype, ta)
        self.assertEqual(new_formula.rhs[0].sign, 1)

    def test_similar_formula_have_the_same_hash(self):
        ta, ca, fa = create_rtypes(
            self.db.session, create_ftype(self.db.session, "bls")
        )
        
        formula1 = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))
        formula2 = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))

        self.assertEqual(hash(formula1), hash(formula2))

    def test_similar_formula_are_equal(self):
        ta, ca, fa = create_rtypes(
            self.db.session, create_ftype(self.db.session, "bls")
        )
        
        formula1 = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))
        formula2 = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))

        self.assertEqual(formula1, formula2)


class RecordTest(DbTestCase):

    def setUp(self):
        super().setUp()
        self.ftype_bls = create_ftype(self.db.session, name="ics")
        self.rtype = create_rtype(
            self.db.session, ftype=self.ftype_bls, name="RECORD_RTYPE"
        )
        self.company = create_company(
            self.db.session, name="RecordTest", isin="#RecordTest"
        )

    def create_record(
        self, timerange, timestamp, value=100, rtype=None, company=None
    ):
        record = Record(
            rtype=rtype or self.rtype, company=company or self.company, 
            timerange=timerange, timestamp=timestamp, value=value
        )
        self.db.session.add(record)
        self.db.session.commit()
        return record     


    def assert_fiscal_year(self, record, fy_start, fy_end):
        fy_start_, fy_end_ = record.determine_fiscal_year()
        self.assertEqual(fy_start, fy_start_)
        self.assertEqual(fy_end, fy_end_)

    def test_determine_fiscal_year_test01(self):
        company = create_company(self.db.session, fiscal_year_start_month=1)
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
        company = create_company(self.db.session, fiscal_year_start_month=7)
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
        company = create_company(self.db.session, fiscal_year_start_month=4)
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
        company = create_company(self.db.session, fiscal_year_start_month=4)
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
        company = create_company(self.db.session, fiscal_year_start_month=6)
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
        company = create_company(self.db.session, fiscal_year_start_month=1)
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

        records = self.db.session.query(Record).\
                  filter(Record.timestamp_start >= date(2015, 10, 1)).all()

        self.assertEqual(len(records), 1)

    def create_record_for_projection_test(
        self, fiscal_year_start_month, timerange, timestamp,
        rtype=None
    ):
        company = create_company(self.db.session,
             fiscal_year_start_month=fiscal_year_start_month
        )
        record = create_record(self.db.session,
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
        ftype = create_ftype(self.db.session, name="bls")
        rtype = create_rtype(self.db.session, ftype, timeframe=RecordType.PIT)
        record = self.create_record_for_projection_test(
            fiscal_year_start_month=1, rtype=rtype,
            timerange=0,
            timestamp = date(2015, 6, 30)
        )
        self.assert_projection(record, 6, 6)

    def test_project_pit_record_timestamp_on_fiscal_year_test02(self):
        ftype = create_ftype(self.db.session, name="bls")
        rtype = create_rtype(self.db.session, ftype, timeframe=RecordType.PIT)
        record = self.create_record_for_projection_test(
            fiscal_year_start_month=7, rtype=rtype,
            timerange=0,
            timestamp = date(2015, 6, 30)
        )
        self.assert_projection(record, 12, 12)

    def test_project_pit_record_timestamp_on_fiscal_year_test03(self):
        ftype = create_ftype(self.db.session, name="bls")
        rtype = create_rtype(self.db.session, ftype, timeframe=RecordType.PIT)
        record = self.create_record_for_projection_test(
            fiscal_year_start_month=7, rtype=rtype,
            timerange=9,
            timestamp = date(2015, 7, 31)
        )
        self.assert_projection(record, 1, 1)

    def test_timerange_of_pit_records_is_always_set_to_zero(self):
        with self.db.session.no_autoflush:
            rtype = create_rtype(
                self.db.session, ftype=create_ftype(self.db.session, name="bls"),
                timeframe=RecordType.PIT
            )
            company = create_company(self.db.session)

            record = Record(
                company=company, rtype=rtype, timerange=12,
                timestamp=date(2015, 12, 31), value=10
            )
            self.db.session.add(record)
            self.db.session.commit()

            self.assertEqual(record.timerange, 0)

    def test_timerange_of_pit_records_cannot_be_change(self):
        with self.db.session.no_autoflush:
            rtype = create_rtype(
                self.db.session, ftype=create_ftype(self.db.session, name="bls"), 
                timeframe=RecordType.PIT
            )
            company = create_company(self.db.session)

            record = Record(
                company=company, rtype=rtype, timerange=0,
                timestamp=date(2015, 12, 31), value=10
            )
            self.db.session.add(record)
            self.db.session.commit()

            record.timerange = 5
            self.db.session.commit()

            self.assertEqual(record.timerange, 0)

    def test_timerange_of_pot_records_can_take_any_number(self):
        with self.db.session.no_autoflush:
            rtype = create_rtype(
                self.db.session, ftype=create_ftype(self.db.session, name="bls"),
                timeframe=RecordType.POT
            )
            company = create_company(self.db.session)

            record = Record(
                company=company, rtype=rtype, timerange=12,
                timestamp=date(2015, 12, 31), value=10
            )
            self.db.session.add(record)
            self.db.session.commit()

            self.assertEqual(record.timerange, 12)


class SyntheticReccordsTest(DbTestCase):
    
    def create_records(self, data):
        records = list()
        for item in data:
            records.append(
                create_record(self.db.session,
                    company=item[0], rtype=item[1], timerange=item[2], 
                    timestamp=item[3], value=item[4]
                )
            )
        return records


    @mock.patch("db.models.Record.create_synthetic_records_for_company")
    def test_create_synthetic_records(self, csr_mock):
        csr_mock.return_value = list()
        
        company1 = create_company(self.db.session)
        company2 = create_company(self.db.session)
        ftype = create_ftype(self.db.session, name="bls")
        rtype = create_rtype(self.db.session, ftype)
        records = self.create_records([
            (company1, rtype, 12, date(2015, 12, 31), 0),
            (company1, rtype, 12, date(2014, 12, 31), 0),
            # (company2, rtype, 12, date(2015, 12, 31), 0)
        ])    
        
        synrecs = Record.create_synthetic_records(self.db.session, records)
        
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
        
        company = create_company(self.db.session)
        ftype = create_ftype(self.db.session, name="bls")
        rtype = create_rtype(self.db.session, ftype)
        records = self.create_records([
            (company, rtype, 12, date(2015, 12, 31), 0),
            # (company, rtype, 12, date(2014, 12, 31), 0),
        ])    
        
        fy_1 = records[0].determine_fiscal_year()
        # fy_2 = records[1].determine_fiscal_year()
        
        synrecs = Record.create_synthetic_records_for_company(
            self.db.session, company, records
        )
        
        self.assertEqual(csr_mock.call_count, 1)

        call_1st_args = csr_mock.call_args_list[0][0]
        self.assertEqual(call_1st_args[2], fy_1)
        self.assertCountEqual(call_1st_args[3], (records[0],))
        
        # call_2nd_args = csr_mock.call_args_list[1][0]
        # self.assertEqual(call_2nd_args[2], (fy_1, fy_2))
        # self.assertCountEqual(call_2nd_args[3], (records[1],))     
        
    def test_get_records_for_company_within_fiscal_year(self):
        company1 = create_company(self.db.session)
        company2 = create_company(self.db.session)
        ftype = create_ftype(self.db.session, name="ics")
        rtype = create_rtype(self.db.session, ftype)
        records = self.create_records([
            (company1, rtype, 12, date(2015, 12, 31), 0),
            (company1, rtype, 3, date(2015, 3, 31), 0),
            (company1, rtype, 12, date(2014, 12, 31), 0),
            (company2, rtype, 12, date(2015, 12, 31), 0)
        ]) 
        
        fiscal_year = utils.FiscalYear(
            start=date(2015, 1, 1), end=date(2015, 12, 31)
        )
        records_ = Record.get_records_for_company_within_fiscal_year(
            self.db.session, company1, fiscal_year
        )

        self.assertEqual(len(records_), 2)
        self.assertCountEqual(records_, (records[0], records[1]))
        
    def test_csr_creates_new_records_pot(self):
        company = create_company(self.db.session)
        ftype = create_ftype(self.db.session, name="bls")
        ta, ca, fa = create_rtypes(self.db.session, ftype, timeframe=RecordType.POT)
        formula = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))
        
        records = self.create_records([
            (company, ca, 12, date(2015, 12, 31), 40),
            (company, fa, 12, date(2015, 12, 31), 60),
        ])
        
        new_records = Record.create_synthetic_records_for_company_within_fiscal_year(
            self.db.session, company=company,
            fiscal_year=utils.FiscalYear(date(2015, 1, 1), date(2015, 12, 31)),
            base_records = [records[0]]
        )
        
        self.assertEqual(len(new_records), 1)
        self.assertEqual(new_records[0].rtype, ta)
        self.assertEqual(new_records[0].value, 100)
        self.assertEqual(new_records[0].timerange, 12)
        self.assertEqual(new_records[0].timestamp, date(2015, 12, 31))

    def test_csr_creates_new_records_pit_and_pot_mixed(self):
        company = create_company(self.db.session)
        ftype_bls = create_ftype(self.db.session, name="bls")
        ftype_ics = create_ftype(self.db.session, name="ics")

        ta = RecordType(name="TOTAL", ftype=ftype_bls, timeframe=RecordType.PIT)
        ca = RecordType(name="CURRENT", ftype=ftype_bls, timeframe=RecordType.PIT)
        fa = RecordType(name="FIXED", ftype=ftype_bls, timeframe=RecordType.PIT)       

        revenues = RecordType(name="REVENUES", ftype=ftype_ics, timeframe=RecordType.POT)
        costs = RecordType(name="COSTS", ftype=ftype_ics, timeframe=RecordType.POT)
        profit = RecordType(name="PROFIT", ftype=ftype_ics, timeframe=RecordType.POT)

        self.db.session.add_all((ta, ca, fa, revenues, costs, profit))
        self.db.session.commit()    

        formula_ta = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))
        formula_profit = create_db_formula(
            self.db.session, profit, ((1, revenues), (-1, costs))
        )

        records = self.create_records([
            (company, ca, 0, date(2015, 12, 31), 40),
            (company, fa, 0, date(2015, 12, 31), 60),
            (company, revenues, 12, date(2015, 12, 31), 100),
            (company, costs, 12, date(2015, 12, 31), 80),
        ]) 

        new_records = Record.create_synthetic_records_for_company_within_fiscal_year(
            self.db.session, company=company,
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
        company = create_company(self.db.session)
        ftype = create_ftype(self.db.session, name="bls")
        ta, ca, fa = create_rtypes(self.db.session, ftype, timeframe=RecordType.PIT)
        formula = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))
        
        records = self.create_records([
            (company, ca, 12, date(2015, 12, 31), 40),
            (company, fa, 12, date(2015, 12, 31), 60),
        ]) 
        
        new_records = Record.create_synthetic_records_for_company_within_fiscal_year(
            self.db.session, company=company,
            fiscal_year=utils.FiscalYear(date(2015, 1, 1), date(2015, 12, 31)),
            base_records = [records[0]]
        )

        self.assertEqual(len(new_records), 1)
        self.assertEqual(new_records[0].rtype, ta)
        self.assertEqual(new_records[0].value, 100)
        self.assertEqual(new_records[0].timerange, 0)
        self.assertEqual(new_records[0].timestamp, date(2015, 12, 31))

    def test_csr_creates_new_records_with_timerange(self):
        company = create_company(self.db.session)
        ftype = create_ftype(self.db.session, name="test")
        ta, ca, fa = create_rtypes(self.db.session, ftype)
        
        records = self.create_records([
            (company, ta, 3, date(2015, 3, 31), 40),
            (company, ta, 6, date(2015, 6, 30), 60),
        ])        
        
        new_records = Record.create_synthetic_records_for_company_within_fiscal_year(
            self.db.session, company=company,
            fiscal_year=utils.FiscalYear(date(2015, 1, 1), date(2015, 12, 31)),
            base_records = [records[0]]
        )

        self.assertEqual(len(new_records), 1)
        self.assertEqual(new_records[0].rtype, ta)
        self.assertEqual(new_records[0].value, 20)
        self.assertEqual(new_records[0].timerange, 3)
        self.assertEqual(new_records[0].timestamp, date(2015, 6, 30))

    def test_csr_updates_already_existing_synthetic_records(self):
        with self.db.session.no_autoflush:
            company = create_company(self.db.session)
            ta, ca, fa = create_rtypes(
                self.db.session, create_ftype(self.db.session, name="cfs"),
                timeframe=RecordType.POT
            )
            formula = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))
            
            records = self.create_records([
                (company, ca, 12, date(2018, 12, 31), 120), # updated from 40 to 120
                (company, fa, 12, date(2018, 12, 31), 60),
                (company, ta, 12, date(2018, 12, 31), 100) # previous synthetic record
            ]) 
            self.assertEqual(records[2].rtype, ta)
            records[2].synthetic = True
            self.db.session.commit()

            new_records = Record.create_synthetic_records_for_company_within_fiscal_year(
                self.db.session, company=company,
                fiscal_year=utils.FiscalYear(date(2018, 1, 1), date(2018, 12, 31)),
                base_records = [records[0]]
            ) 

            self.assertEqual(len(new_records), 1)
            self.assertEqual(new_records[0], records[2])
            self.assertEqual(new_records[0].value, 180)

    def test_csr_creates_synthetic_records_from_synthetic_records(self):
        company = create_company(self.db.session)
        ftype_ics = create_ftype(self.db.session, name="ics", )
        revenues = RecordType(name="REVENUES", ftype=ftype_ics, timeframe=RecordType.POT)
        costs = RecordType(name="COSTS", ftype=ftype_ics, timeframe=RecordType.POT)
        profit = RecordType(name="PROFIT", ftype=ftype_ics, timeframe=RecordType.POT)

        formula_profit = create_db_formula(
            self.db.session, profit, ((1, revenues), (-1, costs))
        )

        records = self.create_records([
            (company, revenues, 6, date(2015, 6, 30), 120),
            (company, revenues, 6, date(2015, 12, 31), 80),
            (company, revenues, 12, date(2015, 12, 31), 200)
        ]) 
        records[2].synthetic = True
        self.db.session.commit()

        record = create_record(self.db.session,
            company=company, rtype=costs, timerange=12,
            timestamp=date(2015, 12, 31), value=100
        )

        new_records = Record.create_synthetic_records_for_company_within_fiscal_year(
            self.db.session, company=company,
            fiscal_year=utils.FiscalYear(date(2015, 1, 1), date(2015, 12, 31)),
            base_records = [record]
        )   

        self.assertEqual(len(new_records), 1)
        self.assertEqual(new_records[0].rtype, profit)
        self.assertEqual(new_records[0].value, 100)


class FinancialStatementTest(DbTestCase):

    def test_insert_default_ftypes(self):
        FinancialStatement.insert_defaults(self.db.session)
        self.db.session.commit()

        self.assertEqual(self.db.session.query(FinancialStatement).count(), 3)
        self.db.session.query(FinancialStatement).filter_by(name="bls").one()
        self.db.session.query(FinancialStatement).filter_by(name="ics").one()
        self.db.session.query(FinancialStatement).filter_by(name="cfs").one()


class FinancialStatementLayoutTest(DbTestCase):

    def setUp(self):
        super().setUp()
        FinancialStatement.insert_defaults(self.db.session)

    def get_ftype(self, name):
        return self.db.session.query(FinancialStatement).\
                    filter_by(name=name).one()

    def test_create_relation_with_record_type_test01(self):
        fs = FinancialStatementLayout(ftype=self.get_ftype("bls"))
        rtype = RecordType(
            name="TOTAL_ASSETS", ftype=self.get_ftype("bls"),
            timeframe=RecordType.POT
        )

        assoc = RTypeFSchemaAssoc(position=1)
        assoc.rtype = rtype
        assoc.fschema = fs
        self.db.session.add(assoc)
        self.db.session.commit()

        self.assertEqual(len(fs.rtypes), 1)
        self.assertEqual(fs.rtypes[0].rtype, rtype)
        self.assertEqual(fs.rtypes[0].position, 1)
        self.assertEqual(rtype.fschemas[0].fschema, fs)

    def test_create_relation_with_record_type_test02(self):
        fs = FinancialStatementLayout(ftype=self.get_ftype("bls"))
        rtype = RecordType(
            name="TOTAL_ASSETS", ftype=self.get_ftype("bls"),
            timeframe=RecordType.POT
        )
        self.db.session.add_all((fs, rtype))
        self.db.session.commit()

        fs.rtypes.append(RTypeFSchemaAssoc(rtype=rtype, position=1))
        self.db.session.commit()

        self.assertEqual(len(fs.rtypes), 1)
        self.assertEqual(fs.rtypes[0].rtype, rtype)
        self.assertEqual(fs.rtypes[0].position, 1)
        self.assertEqual(rtype.fschemas[0].fschema, fs)

    def test_create_relation_with_method_append_rtype(self):
        fs = FinancialStatementLayout(ftype=self.get_ftype("bls"))
        rtype = RecordType(
            name="TOTAL_ASSETS", ftype=self.get_ftype("bls"),
            timeframe=RecordType.POT
        )
        self.db.session.add_all((fs, rtype))
        self.db.session.commit()

        fs.append_rtype(rtype, 1)
        self.db.session.commit()

        self.assertEqual(len(fs.rtypes), 1)
        self.assertEqual(fs.rtypes[0].rtype, rtype)
        self.assertEqual(fs.rtypes[0].position, 1)
        self.assertEqual(rtype.fschemas[0].fschema, fs)

    def test_get_default_repr(self):
        fs = FinancialStatementLayout(ftype=self.get_ftype("bls"))
        fs.reprs.append(FinancialStatementLayoutRepr(lang="PL", value="Bilans"))
        fs.reprs.append(FinancialStatementLayoutRepr(
            lang="EN", value="Balance Sheet", default=True
        ))
        self.db.session.add(fs)
        self.db.session.commit()

        fs_repr = fs.default_repr

        self.assertEqual(fs_repr.lang, "EN")
        self.assertEqual(fs_repr.value, "Balance Sheet")

    def test_for_retrieving_records_in_accordance_with_schema(self):
        company = create_company(self.db.session, name="Test", isin="#TEST")
        company_fake = create_company(self.db.session, name="Fake", isin="#FAKSE")
        ta, ca, fa = create_rtypes(self.db.session, timeframe=RecordType.PIT)
        records = create_records(self.db.session, [
            (company, ta, 0, date(2015, 12, 31), 100),
            (company, fa, 0, date(2015, 12, 31), 50),
            (company_fake, fa, 0, date(2014, 12, 31), 100),
            (company_fake, ca, 0, date(2014, 12, 31), 50)
        ])  
        self.db.session.add_all(records)
        schema = FinancialStatementLayout()
        schema.append_rtype(fa, 0)
        schema.append_rtype(ca, 1)
        schema.append_rtype(ta, 2)
        self.db.session.add(schema)
        self.db.session.commit()

        data = schema.get_records(company=company, timerange=12)

        self.assertCountEqual(data, records[:2])

    def test_get_records_returns_empty_list_when_no_records(self):
        company = create_company(self.db.session, name="Test", isin="#TEST")
        self.db.session.add(company)
        ta, ca, fa = create_rtypes(self.db.session)
        schema = FinancialStatementLayout()
        schema.append_rtype(fa, 0)
        schema.append_rtype(ca, 1)
        schema.append_rtype(ta, 2)
        self.db.session.add(schema)
        self.db.session.commit()

        data = schema.get_records(company=company, timerange=0)

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)
        
    def test_get_pot_records_for_nonzero_timerange(self):
        company = create_company(self.db.session, name="Test", isin="#TEST")
        ta, ca, fa = create_rtypes(self.db.session, timeframe=RecordType.PIT)
        ref_records = create_records(self.db.session, [
            (company, ta,  0, date(2015,  3, 31), 100),
            (company, fa,  0, date(2015, 12, 31),  50),
            (company, fa,  0, date(2016,  6, 30),  90),
            (company, ca,  0, date(2016, 12, 31), 120)
        ])  
        self.db.session.add_all(ref_records)
        schema = FinancialStatementLayout()
        schema.append_rtype(fa, 0)
        schema.append_rtype(ca, 1)
        schema.append_rtype(ta, 2)
        self.db.session.add(schema)
        self.db.session.commit()

        wal_records = schema.get_records(company=company, timerange=12)

        self.assertEqual(len(wal_records), 2)
        self.assertCountEqual(wal_records, [ref_records[1], ref_records[3]])

    def test_get_pit_and_pot_records_in_single_query(self):
        company = create_company(
            self.db.session, name="Test", isin="#TEST",
            fiscal_year_start_month=7
        )
        rtype_assets = create_rtype(
            self.db.session, self.get_ftype("bls"), 
            name="ASSETS", timeframe=RecordType.PIT
        )
        rtype_revenues = create_rtype(
            self.db.session, self.get_ftype("ics"), 
            name="REVENUES", timeframe=RecordType.POT
        )
        ref_records = create_records(self.db.session, [
            (company, rtype_assets,    0, date(2015,  9, 30), 100),
            (company, rtype_revenues,  3,  date(2015, 9, 30),  50),
            (company, rtype_assets,    0, date(2016,  6, 30),  90),
            (company, rtype_revenues,  12, date(2016, 6, 30), 120)
        ])  
        self.db.session.add_all(ref_records)
        schema = FinancialStatementLayout()
        schema.append_rtype(rtype_assets, 0)
        schema.append_rtype(rtype_revenues, 1)
        self.db.session.add(schema)
        self.db.session.commit()

        wal_records = schema.get_records(company=company, timerange=12)

        self.assertEqual(len(wal_records), 2)
        self.assertCountEqual(wal_records, [ref_records[2], ref_records[3]])    


class CompanyTest(DbTestCase):
    
    def test_determine_fiscal_year_for_standard_fiscal_year(self):
        company = Company(name="TEST", isin="#TEST", fiscal_year_start_month=1)
        
        fiscal_year = company.determine_fiscal_year(start_year=2015)
        
        self.assertEqual(fiscal_year[0], date(2015, 1, 1))
        self.assertEqual(fiscal_year[1], date(2015, 12, 31))
        
    def test_determine_fiscal_year_for_nonstanard_fiscal_year(self):
        company = Company(name="TEST", isin="#TEST", fiscal_year_start_month=7)
        
        fiscal_year = company.determine_fiscal_year(start_year=2014)
        
        self.assertEqual(fiscal_year[0], date(2014, 7, 1))
        self.assertEqual(fiscal_year[1], date(2015, 6, 30))   
        
    def test_determine_fiscal_months_for_3months_timerange(self):
        company = Company(name="TEST", isin="#TEST", fiscal_year_start_month=1)
        
        fiscal_months = company.determine_fiscal_months(3)
        
        self.assertCountEqual(fiscal_months, (3, 6, 9, 12))
        
    def test_determine_fiscal_months_for_6months_timerange(self):
        company = Company(name="TEST", isin="#TEST", fiscal_year_start_month=1)
        
        fiscal_months = company.determine_fiscal_months(6)
        
        self.assertCountEqual(fiscal_months, (6, 12))       
        
    def test_determine_fiscal_months_for_12months_timerange(self):
        company = Company(name="TEST", isin="#TEST", fiscal_year_start_month=1)
        
        fiscal_months = company.determine_fiscal_months(12)
        
        self.assertCountEqual(fiscal_months, (12,))   
        
    def test_determine_fiscal_months_for_3months_timerange_test2(self):
        company = Company(name="TEST", isin="#TEST", fiscal_year_start_month=7)
        
        fiscal_months = company.determine_fiscal_months(3)
        
        self.assertCountEqual(fiscal_months, (9, 12, 3, 6))
        
    def test_determine_fiscal_months_for_6months_timerange_test2(self):
        company = Company(name="TEST", isin="#TEST", fiscal_year_start_month=7)
        
        fiscal_months = company.determine_fiscal_months(6)
        
        self.assertCountEqual(fiscal_months, (12, 6))       
        
    def test_determine_fiscal_months_for_12months_timerange_test2(self):
        company = Company(name="TEST", isin="#TEST", fiscal_year_start_month=7)
        
        fiscal_months = company.determine_fiscal_months(12)
        
        self.assertCountEqual(fiscal_months, (6,))   