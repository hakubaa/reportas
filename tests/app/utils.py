from app import db
from db.models import (
    Company, RecordType, RecordFormula, FormulaComponent, Record,
    FinancialStatementType, FinancialStatementSchema, RTypeFSchemaAssoc,
    FinancialStatementSchemaRepr, FinancialStatementSchema
)


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


def create_rtypes(ftype=None, timeframe="pot"):
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


def create_records(data):
    records = list()
    for item in data:
        records.append(
            create_record(
                company=item[0], rtype=item[1], timerange=item[2], 
                timestamp=item[3], value=item[4]
            )
        )
    return records

def create_db_formula(left, right):
    formula = RecordFormula(rtype=left)
    db.session.add(formula)
    for item in right:
        formula.add_component(rtype=item[1], sign=item[0])
    db.session.commit()
    return formula