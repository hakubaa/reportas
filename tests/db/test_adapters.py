from datetime import date

from db.models import (
    Company, RecordType, RecordFormula, FormulaComponent, Record,
    FinancialStatement
)
from db.adapters.rparser import (
    convert_db_formula, convert_db_record, DictRecordsDataset,
    convert_db_records, convert_rparser_record,
    project_timeframe_onto_fiscal_year, create_synthetic_records
)
import rparser.synthetic as rparser

from tests.db import DbTestCase
from tests.db.utils import *


class TestRParserAdapters(DbTestCase):

    def test_convert_db_formula(self):
        ta, ca, fa = create_rtypes(self.db.session)
        db_formula = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))

        formula = convert_db_formula(db_formula)

        self.assertIsInstance(formula, rparser.Formula)
        self.assertEqual(formula.spec, ta)
        self.assertEqual(len(formula.rhs), 2)
        self.assertEqual(formula.rhs[0].spec, ca)
        self.assertEqual(formula.rhs[1].spec, fa)

    def test_convert_db_record(self):
        ta, ca, fa = create_rtypes(self.db.session) 
        company = create_company(self.db.session, name="TEST", isin="TEST#1")
        record_db = Record(
            company=company, rtype=ta, value=100, timerange=6,
            timestamp=date(2016, 6, 30)
        )

        record = convert_db_record(record_db)

        self.assertIsInstance(record.spec, rparser.TimeframeSpec)
        self.assertEqual(record.spec.spec, ta)
        self.assertEqual(record.spec.timeframe, rparser.Timeframe(1, 6))
        self.assertEqual(record.value, 100)

    def test_create_dataset_from_records(self):
        ta, ca, fa = create_rtypes(self.db.session) 
        company = create_company(self.db.session, name="TEST", isin="TEST#1")
        r1 = Record(company=company, rtype=ta, value=100, timerange=6,
                    timestamp=date(2016, 6, 30))
        r2 = Record(company=company, rtype=fa, value=40, timerange=6,
                    timestamp=date(2016, 6, 30))
        r3 = Record(company=company, rtype=ca, value=60, timerange=6,
                    timestamp=date(2016, 6, 30))

        dataset = DictRecordsDataset.create_from_records(
            convert_db_records((r1, r2, r3))
        )

        self.assertEqual(len(dataset), 3)

        index = rparser.TimeframeSpec(spec=ta, timeframe=rparser.Timeframe(1, 6))
        self.assertEqual(dataset[index]["value"], 100)

        index = rparser.TimeframeSpec(spec=fa, timeframe=rparser.Timeframe(1, 6))
        self.assertEqual(dataset[index]["value"], 40)

        index = rparser.TimeframeSpec(spec=ca, timeframe=rparser.Timeframe(1, 6))
        self.assertEqual(dataset[index]["value"], 60)
        
    def test_convert_rparser_record_into_db_record(self):
        ta, ca, fa = create_rtypes(self.db.session) 
        company = create_company(self.db.session, name="TEST", isin="TEST#1")
        
        record = rparser.Record(
            spec=rparser.TimeframeSpec(
                spec=ta, timeframe=rparser.Timeframe(1,3)
            ), value=10, synthetic=False
        )
        
        record_db = convert_rparser_record(
            self.db.session, record, company, 
            rparser.Timeframe(start=date(2015, 1, 1), end=date(2015, 12, 31))
        )
        
        self.assertIsInstance(record_db, Record)
        self.assertEqual(record_db.rtype, ta)
        self.assertEqual(record_db.company, company)
        self.assertEqual(record_db.value, record.value)
        self.assertEqual(record_db.timerange, 3)
        self.assertEqual(record_db.timestamp, date(2015, 3, 31))
        
    def test_project_timeframe_onto_fiscal_year_test01(self):
        timestamp_range = project_timeframe_onto_fiscal_year(
            rparser.Timeframe(1, 3), 
            rparser.Timeframe(date(2015, 1, 1), date(2015, 12, 31))
        )
        
        self.assertEqual(timestamp_range.start, date(2015, 1, 1))
        self.assertEqual(timestamp_range.end, date(2015, 3, 31))
        
    def test_project_timeframe_onto_fiscal_year_test02(self):
        timestamp_range = project_timeframe_onto_fiscal_year(
            rparser.Timeframe(1, 6), 
            rparser.Timeframe(date(2014, 7, 1), date(2015, 6, 30))
        )
        
        self.assertEqual(timestamp_range.start, date(2014, 7, 1))
        self.assertEqual(timestamp_range.end, date(2014, 12, 31)) 
        
    def test_project_timeframe_onto_fiscal_year_test03(self):
        timestamp_range = project_timeframe_onto_fiscal_year(
            rparser.Timeframe(1, 12), 
            rparser.Timeframe(date(2014, 7, 1), date(2015, 6, 30))
        )
        
        self.assertEqual(timestamp_range.start, date(2014, 7, 1))
        self.assertEqual(timestamp_range.end, date(2015, 6, 30))  
        
    def test_create_synthetic_records(self):
        ftype = create_ftype(
            self.db.session, name="bls", timeframe=FinancialStatement.PIT
        )
        
        ta, ca, fa = create_rtypes(self.db.session, ftype=ftype) 
        db_formula = create_db_formula(self.db.session, ta, ((1, ca), (1, fa)))
        company = create_company(self.db.session, name="TEST", isin="TEST#1")
        record_fa = Record(
            rtype=fa, company=company, value=100, timerange=0,
            timestamp=date(2015, 12, 31)
        )
        record_ca = Record(
            rtype=ca, company=company, value=900, timerange=0,
            timestamp=date(2015, 12, 31)
        )
        self.db.session.add_all((record_fa, record_ca))
        self.db.session.commit()
        
        records = create_synthetic_records(
            (record_ca,), (record_fa, record_ca), (db_formula,)
        )
        
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].value, 1000)
        self.assertIsInstance(records[0], rparser.Record)