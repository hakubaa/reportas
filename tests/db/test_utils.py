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


def create_rtypes(ftype=None):
    if not ftype:
        ftype = create_ftype()
    total_assets = RecordType(name="TOTAL_ASSETS", ftype=ftype)
    current_assets = RecordType(name="CURRENT_ASSETS", ftype=ftype)
    fixed_assets = RecordType(name="FIXED_ASSETS", ftype=ftype)
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
    

def create_formula(left, right):
    new_formula = utils.Formula(utils.Formula.Component(left, 0))
    for item in right:
        new_formula.add_component(utils.Formula.Component(item[0], item[1]))
    return new_formula

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

    def test_represent_records_as_matrix(self):
        company = create_company()
        ftype = create_ftype("bls")
        rtype1 = create_rtype(name="NET_PROFIT", ftype=ftype, timeframe="pot")
        rtype2 = create_rtype(name="REVENUE", ftype=ftype, timeframe="pot")
        records = self.create_records([
            (company, rtype1, 3, date(2015, 3, 31), 1),
            (company, rtype1, 6, date(2015, 6, 30), 2),
            (company, rtype2, 9, date(2015, 9, 30), 3),
            (company, rtype2, 12, date(2015, 12, 31), 4)
        ])    
        
        recmat = utils.represent_records_as_matrix(records)

        self.assertEqual(len(recmat), 2)
        self.assertCountEqual(recmat.keys(), (rtype1, rtype2))
        self.assertEqual(recmat[rtype1][utils.TimeRange(1, 3)], 1)
        self.assertEqual(recmat[rtype1][utils.TimeRange(1, 6)], 2)
        self.assertEqual(recmat[rtype2][utils.TimeRange(1, 9)], 3)
        self.assertEqual(recmat[rtype2][utils.TimeRange(1, 12)], 4)


class UtilsFormulaTest(AppTestCase):

    def test_convert_db_formula(self):
        ta, ca, fa = create_rtypes()
        db_formula = create_db_formula(ta, ((1, ca), (1, fa)))

        formula = utils.convert_db_formula(db_formula)

        self.assertIsInstance(formula, utils.Formula)
        self.assertEqual(formula.lhs.rtype, ta)
        self.assertEqual(len(formula.rhs), 2)

    def test_extend_formula_with_timerange(self):
        ta, ca, fa = create_rtypes()
        db_formula = create_db_formula(ta, ((1, ca), (1, fa)))

        formula = utils.convert_db_formula(db_formula)
        formula = formula.extend_with_timerange(utils.TimeRange(1, 3))

        self.assertIsInstance(formula.lhs, utils.Formula.TimeRangeComponent)
        self.assertTrue(all(
            map(lambda item: item.timerange == utils.TimeRange(1, 3), 
                formula.rhs))
        )

    def test_calculate_formula(self):
        ta, ca, fa = create_rtypes()
        db_formula = create_db_formula(ta, ((1, ca), (1, fa)))

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
        db_formula = create_db_formula(ta, ((1, ca), (1, fa)))

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
        db_formula = create_db_formula(ta, ((1, ca), (1, fa)))

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
            ta, lhs_spec=(0, utils.TimeRange(1, 6)),
            rhs_spec=[(1, utils.TimeRange(1, 3)), (1, utils.TimeRange(4, 6))]
        )

        self.assertTrue(formula.is_calculable(data))
        self.assertEqual(formula.calculate(data), 10)

    def test_similar_formula_have_the_same_hash(self):
        ta, ca, fa = create_rtypes()
        db_formula = create_db_formula(ta, ((1, ca), (1, fa)))

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
        db_formula = create_db_formula(ta, ((1, ca), (1, fa)))

        data = {
            ta: { utils.TimeRange(1, 3): 10 },
            ca: { utils.TimeRange(1, 3): 5 },
            fa: { utils.TimeRange(1, 3): 5 }
        }

        formula1 = utils.convert_db_formula(db_formula)
        formula2 = utils.convert_db_formula(db_formula)

        self.assertEqual(formula1, formula2)

    @mock.patch("db.utils.convert_db_formula")
    def test_convert_multiple_formulas(self, convert_mock):
        convert_mock.return_value = 1
        
        ta, ca, fa = create_rtypes()
        ta_formula = create_db_formula(ta, ((1, ca), (1, fa)))  
        ca_formula = create_db_formula(ca, ((1, ta), (-1, fa)))
        fa_formula = create_db_formula(fa, ((1, ta), (-1, ca)))
        
        formulas = utils.convert_db_formulas((ta_formula, ca_formula, fa_formula))
        
        self.assertEqual(convert_mock.call_count, 3)
        self.assertCountEqual(formulas, [1, 1, 1])
        
        mock_args = [ ca[0][0] for ca in convert_mock.call_args_list ]

        self.assertIn(ta_formula, mock_args)
        self.assertIn(ca_formula, mock_args)
        self.assertIn(fa_formula, mock_args)

    def test_create_db_formulas_transformations(self):
        ta, ca, fa = create_rtypes()
        formula = create_db_formula(ta, ((1, ca), (1, fa)))
        
        new_formulas = utils.create_db_formulas_transformations(formula)
        
        self.assertEqual(len(new_formulas), 2)
        rtypes = [ formula.lhs  for formula in new_formulas ]
        self.assertCountEqual(rtypes, (ca, fa))
        
    @mock.patch("db.utils.create_timerange_formula")
    def test_create_timerange_formulas(self, create_mock):
        ta, ca, fa = create_rtypes()
        
        timerange_formulas = [
            ((0, (1, 3)), [(1, (1, 6)), (-1, (4, 6))]),
            ((0, (1, 6)), [(1, (1, 3)), (1, (4, 6))])
        ]
        formulas = utils.create_timerange_formulas(
            (ta, ca, fa), timerange_formulas
        )
        
        self.assertEqual(create_mock.call_count, 6)
        
    def test_remove_duplicate_formulas(self):
        ta, ca, fa = create_rtypes()
        
        formula_ta = create_formula(ta, [(ca, 1), (fa, 1)])
        formula_ta2 = create_formula(ta, [(ca, 1), (fa, 1)])
        formula_ca = create_formula(ca, [(ta, 1), (fa, -1)])
        
        formulas = utils.remove_duplicated_formulas(
            [formula_ta, formula_ta2, formula_ca]
        )

        self.assertEqual(len(formulas), 2)
        self.assertIn(formula_ta, formulas)
        self.assertIn(formula_ca, formulas)
        
    def test_create_inverted_mapping(self):
        ta, ca, fa = create_rtypes()
        
        formula_ta = create_formula(ta, [(ca, 1), (fa, 1)]).\
                         extend_with_timerange(utils.TimeRange(1, 3))
        formula_ca = create_formula(ca, [(fa, 1)]).\
                         extend_with_timerange(utils.TimeRange(1, 3))
        
        formulas = utils.create_inverted_mapping([formula_ta, formula_ca])
        
        self.assertNotIn(ta, formulas)
        self.assertIn(ca, formulas)
        self.assertIn(fa, formulas)
        self.assertEqual(len(formulas[fa][utils.TimeRange(1, 3)]), 2)
        self.assertEqual(len(formulas[ca][utils.TimeRange(1, 3)]), 1)
        self.assertCountEqual(
            formulas[fa][utils.TimeRange(1, 3)], 
            (formula_ta, formula_ca)
        )
        self.assertCountEqual(
            formulas[ca][utils.TimeRange(1, 3)], (formula_ta,)
        )
        
    def test_csr_returns_list_of_created_records(self):
        ta, ca, fa = create_rtypes()
        formula_ta = create_formula(ta, [(ca, 1), (fa, 1)])\
                         .extend_with_timerange(utils.TimeRange(1, 3))
        fiscal_year = utils.FiscalYear(date(2015, 1, 1), date(2015, 12, 31))
        data = {
            ca: { utils.TimeRange(1, 3): 10 },
            fa: { utils.TimeRange(1, 3): 15 },
            ta: { }
        }
        
        formulas = utils.create_inverted_mapping([formula_ta])

        syn_records = utils.create_synthetic_records(
            (ca, utils.TimeRange(1, 3)), data, formulas
        )

        self.assertEqual(len(syn_records), 1)
        self.assertEqual(syn_records[0]["value"], 25)
        self.assertEqual(syn_records[0]["rtype"], ta)
        self.assertEqual(syn_records[0]["timerange"], utils.TimeRange(1, 3))
        
    def test_csr_updates_data(self):
        ta, ca, fa = create_rtypes()
        formula_ta = create_formula(ta, [(ca, 1), (fa, 1)])\
                         .extend_with_timerange(utils.TimeRange(1, 3))
        data = {
            ca: { utils.TimeRange(1, 3): 10 },
            fa: { utils.TimeRange(1, 3): 15 }
        }
        
        formulas = utils.create_inverted_mapping([formula_ta])

        syn_records = utils.create_synthetic_records(
            (ca, utils.TimeRange(1, 3)), data, formulas
        )       

        self.assertIn(ta, data)
        self.assertIn(utils.TimeRange(1, 3), data[ta])
        self.assertEqual(
            data[ta][utils.TimeRange(1, 3)], 
            syn_records[0]["value"]
        )
    
    def test_csr_creates_new_records_recurrently(self):
        ta, ca, fa = create_rtypes()
        ftype = db.session.query(FinancialStatementType).one()
        lb = create_rtype(name="TOTAL LIABILITIES", ftype=ftype)
        formula_ta = create_formula(ta, [(ca, 1), (fa, 1)])\
                         .extend_with_timerange(utils.TimeRange(1, 3))
        formula_lb = create_formula(lb, [(ta, 1)])\
                         .extend_with_timerange(utils.TimeRange(1, 3))
        
        formulas = utils.create_inverted_mapping([formula_ta, formula_lb])
        
        data = {
            ca: { utils.TimeRange(1, 3): 10 },
            fa: { utils.TimeRange(1, 3): 15 }
        }
        
        syn_records = utils.create_synthetic_records(
            (ca, utils.TimeRange(1, 3)), data, formulas
        )   

        self.assertEqual(len(syn_records), 2)
        lb_record = next(filter(lambda item: item["rtype"] == lb, syn_records))
        self.assertEqual(lb_record["value"], 25)
        self.assertEqual(lb_record["timerange"], utils.TimeRange(1, 3))
        self.assertIn(lb, data)
        self.assertEqual(data[lb][utils.TimeRange(1, 3)], 25)
        
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