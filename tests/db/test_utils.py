import unittest
from unittest import mock
import json
from datetime import date

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref

from db.models import (
    Company, RecordType, RecordFormula, FormulaComponent, Record,
    FinancialStatement
)
from db.core import Model, VersionedModel
import db.utils as utils
import db.tools as tools

from tests.db import DbTestCase

#-------------------------------------------------------------------------------
# Utils
#-------------------------------------------------------------------------------

def create_ftype(session, name="bls"):
    fst = FinancialStatement(name=name)
    session.add(fst)
    session.commit()
    return fst

def create_rtype(session, name, ftype, timeframe="pot"):
    total_assets = RecordType(name=name, ftype=ftype, timeframe=timeframe)
    session.add(total_assets)
    session.commit()    
    return total_assets

def counter_decorator(func):
    func.counter = 0
    return func
    
@counter_decorator
def create_company(session, name=None, isin=None, fiscal_year_start_month = 1):
    if not name:
        name = "TEST#%s" % create_company.counter
    if not isin:
        isin = "#TEST#%s" % create_company.counter
    create_company.counter += 1
    company = Company(
        name=name, isin=isin, fiscal_year_start_month=fiscal_year_start_month
    )
    session.add(company)
    session.commit()
    return company

def create_record(session, **kwargs):
    record = Record(**kwargs)
    session.add(record)
    session.commit()
    return record

#-------------------------------------------------------------------------------

class TestUtils(DbTestCase):
    
    def create_records(self, data):
        records = list()
        for item in data:
            records.append(
                create_record(
                    self.db.session,
                    company=item[0], rtype=item[1], timerange=item[2], 
                    timestamp=item[3], value=item[4]
                )
            )
        return records

    def test_group_records_by_company(self):
        company1 = create_company(self.db.session)
        company2 = create_company(self.db.session)
        rtype = create_rtype(self.db.session, "ASSETS", 
                             create_ftype(self.db.session, "bls"))
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
        company = create_company(self.db.session)  
        rtype = create_rtype(self.db.session, "ASSETS", 
                             create_ftype(self.db.session, "bls"))
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
      