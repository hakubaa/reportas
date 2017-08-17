from db import models
from app import db


def create_company(name, isin):
    company = models.Company(name=name, isin=isin)
    db.session.add(company)
    db.session.commit()
    return company

def create_ftype(name):
    ftype = models.FinancialStatementType(name=name)
    db.session.add(ftype)
    db.session.commit()
    return ftype
    
def create_fschema(ftype, **kwargs):
    fs = models.FinancialStatementSchema(ftype=ftype)
    kwargs.update(dict(default=1))
    fs.reprs.append(models.FinancialStatementSchemaRepr(**kwargs))
    db.session.add(fs)
    db.session.commit()
    return fs
