import unittest
from unittest import mock
import json
from datetime import date

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref

from app import db
from db.models import (
    Company, RecordType, RecordFormula, FormulaComponent, Record,
    FinancialStatementType
)
from db.core import Model, VersionedModel
import db.utils as utils
import db.tools as tools

from tests.app import AppTestCase

#-------------------------------------------------------------------------------

def create_ftype(name="bls"):
    fst = FinancialStatementType(name=name)
    db.session.add(fst)
    db.session.commit()
    return fst


def create_rtype(name, ftype, timeframe="pot"):
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


def create_rtypes(ftype=None, timeframe="pot"):
    if not ftype:
        ftype = create_ftype()
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

class UtilsForSyntheticReccordsTest(AppTestCase):
    
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
        rtype = create_rtype("ASSETS", create_ftype("bls"))
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
        rtype = create_rtype("ASSETS", create_ftype("bls"))
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


class UtilsFormulaTest(AppTestCase):
        
    def test_project_timerange_onto_fiscal_year_test01(self):
        timestamp_range = utils.project_timerange_onto_fiscal_year(
            utils.TimeRange(1, 3), 
            utils.FiscalYear(date(2015, 1, 1), date(2015, 12, 31))
        )
        
        self.assertEqual(timestamp_range.start, date(2015, 1, 1))
        self.assertEqual(timestamp_range.end, date(2015, 3, 31))
        
    def test_project_timerange_onto_fiscal_year_test02(self):
        timestamp_range = utils.project_timerange_onto_fiscal_year(
            utils.TimeRange(1, 6), 
            utils.FiscalYear(date(2014, 7, 1), date(2015, 6, 30))
        )
        
        self.assertEqual(timestamp_range.start, date(2014, 7, 1))
        self.assertEqual(timestamp_range.end, date(2014, 12, 31)) 
        
    def test_project_timerange_onto_fiscal_year_test03(self):
        timestamp_range = utils.project_timerange_onto_fiscal_year(
            utils.TimeRange(1, 12), 
            utils.FiscalYear(date(2014, 7, 1), date(2015, 6, 30))
        )
        
        self.assertEqual(timestamp_range.start, date(2014, 7, 1))
        self.assertEqual(timestamp_range.end, date(2015, 6, 30))        