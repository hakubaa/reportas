from datetime import date

from db.models import (
    Company, RecordType, RecordFormula, FormulaComponent, Record,
    FinancialStatementType
)
from db.adapters.rparser import (
    convert_db_formula, convert_db_record, DictRecordsDataset,
    convert_db_records
)
import rparser.synthetic as rparser

from tests.db import DbTestCase


#-------------------------------------------------------------------------------
# Utils
#-------------------------------------------------------------------------------

def create_db_formula(session, left, right):
    formula = RecordFormula(rtype=left)
    session.add(formula)
    for item in right:
        formula.add_component(rtype=item[1], sign=item[0])
    session.commit()
    return formula


def create_ftype(session, name="bls"):
    fst = FinancialStatementType(name=name)
    session.add(fst)
    session.commit()
    return fst


def create_rtypes(session, ftype=None, timeframe="pot"):
    if not ftype:
        ftype = create_ftype(session)
    total_assets = RecordType(
        name="TOTAL_ASSETS", ftype=ftype, timeframe=timeframe
    )
    current_assets = RecordType(
        name="CURRENT_ASSETS", ftype=ftype, timeframe=timeframe
    )
    fixed_assets = RecordType(
        name="FIXED_ASSETS", ftype=ftype, timeframe=timeframe
    )
    session.add_all((total_assets, current_assets, fixed_assets))
    session.commit()    
    return total_assets, current_assets, fixed_assets


def create_company(session, name, isin, fiscal_year_start_month = 1):
    company = Company(
        name=name, isin=isin, fiscal_year_start_month=fiscal_year_start_month
    )
    session.add(company)
    session.commit()
    return company

#-------------------------------------------------------------------------------

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
        ta, ca, fa = create_rtypes(self.db.session, timeframe="pot") 
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
        ta, ca, fa = create_rtypes(self.db.session, timeframe="pot") 
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