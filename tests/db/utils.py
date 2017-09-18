from db.models import (
    Company, RecordType, RecordFormula, FormulaComponent, Record,
    FinancialStatement, FinancialStatementLayout, RTypeFSchemaAssoc,
    FinancialStatementLayoutRepr
)


def create_ftype(session, name="bls"):
    ftype = FinancialStatement(name=name)
    session.add(ftype)
    session.commit()
    return ftype


def create_rtype(session, ftype, name="TOTAL_ASSETS", timeframe=RecordType.POT):
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


def create_rtypes(session, ftype=None, timeframe=RecordType.POT):
    if not ftype:
        ftype = session.query(FinancialStatement).filter_by(name="bls").first()
        if not ftype:
            ftype = create_ftype(session, name="bls")
            
    common = dict(ftype=ftype, timeframe=timeframe)
    total_assets = RecordType(name="TOTAL_ASSETS", **common)
    current_assets = RecordType(name="CURRENT_ASSETS", **common)
    fixed_assets = RecordType(name="FIXED_ASSETS", **common)
    session.add_all((total_assets, current_assets, fixed_assets))
    session.commit()    
    return total_assets, current_assets, fixed_assets


def create_records(session, data):
    records = list()
    for item in data:
        records.append(
            create_record(session, 
                company=item[0], rtype=item[1], timerange=item[2], 
                timestamp=item[3], value=item[4]
            )
        )
    return records

def create_db_formula(session, left, right):
    formula = RecordFormula(rtype=left)
    session.add(formula)
    for item in right:
        formula.add_component(rtype=item[1], sign=item[0])
    session.commit()
    return formula