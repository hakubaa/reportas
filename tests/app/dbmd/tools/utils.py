from db import models
from app import db


def create_company(name="TEST", isin="#TEST"):
    company = models.Company(name=name, isin=isin)
    db.session.add(company)
    db.session.commit()
    return company

def create_ftype(name):
    ftype = models.FinancialStatement(name=name)
    db.session.add(ftype)
    db.session.commit()
    return ftype

def create_rtype(**kwargs):
    rtype = models.RecordType(**kwargs)
    db.session.add(rtype)
    db.session.commit()
    return rtype
    
def create_fschema(ftype, **kwargs):
    fs = models.FinancialStatementLayout(ftype=ftype)
    kwargs.update(dict(default=1))
    fs.reprs.append(models.FinancialStatementLayoutRepr(**kwargs))
    db.session.add(fs)
    db.session.commit()
    return fs
