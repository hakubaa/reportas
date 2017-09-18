import itertools
from datetime import datetime
from concurrent import futures
import warnings
from collections import namedtuple

import requests
from sqlalchemy.exc import IntegrityError
from bs4 import BeautifulSoup

from db.models import (
    Report, RecordType, RecordTypeRepr, Record, Company, CompanyRepr, Sector,
    FinancialStatement
)
import db.utils as utils
from rparser.nlp import find_ngrams
import rparser.utils as putil



def upload_companies(session, data):
    '''Update companies in db.'''
    for item in data:
        try:
            sector_name = item.pop("sector", None)
            instance = Company.get_or_create(
                session, defaults=item, isin=item.get("isin", item.get("ISIN"))
            )
            session.add(instance)
            if sector_name:
                sector = Sector.get_or_create(session, name=sector_name)
                session.add(sector)
                instance.sector = sector
        except KeyError:
            warnings.warn(
                "Record without ISIN number. Name: '{}'".
                    format(item.get("name", None))
            )
            continue
        if instance.id:
            for key, value in item.items():
                setattr(instance, key, value)               


def upload_records_spec(session, spec, default_timeframe="pit"):
    '''
    Create RecordType & RecordTypeRepr records in db in accordance with 
    specification.
    '''
    try: # ensure spec is iterable
        iter(spec)
    except TypeError:
        spec = [spec]

    timeframe_mapper = {
        "pit": RecordType.PIT, "pot": RecordType.POT
    }

    for record_spec in spec:
        ftype = session.query(FinancialStatement).\
                    filter_by(name=record_spec["statement"]).one()
        rtype = RecordType(
            name=record_spec["name"], ftype=ftype,
            timeframe=timeframe_mapper[record_spec.get("timeframe", default_timeframe)]
        )
        session.add(rtype)
        for repr_spec in record_spec.get("repr", list()):
            repr_spec["rtype"] = rtype
            rtype_repr = RecordTypeRepr.create(session, **repr_spec)


def get_records_reprs(session, ftype, lang="PL", n=1, min_len=2, 
                      remove_non_alphabetic=True):
    '''Get list of items representations for selected statement.'''
    spec = list()
    records = session.query(RecordTypeRepr).join(RecordType).\
                  filter(RecordType.ftype == ftype,
                         RecordTypeRepr.lang.ilike(lang)
                  ).all()
    for record in records:
        nigrams = find_ngrams(
            putil.remove_non_ascii(record.value), n=n, min_len=min_len,
            remove_non_alphabetic=remove_non_alphabetic
        )
        spec.append(
            dict(
                id=record.rtype_id,
                name=record.rtype.name,
                ngrams=nigrams
            )
        )

    return spec


def get_companies_reprs(session):
    '''Return list of companies (isin) with their reprpresentations.'''
    keys = ("isin", "repr", "id")
    values = session.query(Company.isin, Company.fullname, Company.id).\
                 filter(Company.fullname != "").all()
    cspec = list(map(lambda item: dict(zip(keys, item)), values))

    keys = ("repr", "isin", "id")
    values = session.query(CompanyRepr.value, Company.isin, Company.id).\
                 join(Company).filter(CompanyRepr.value != "").all()
    cspec.extend(map(lambda item: dict(zip(keys, item)), values))

    return cspec


def create_vocabulary(session, min_len=2, remove_non_alphabetic=True,
                      remove_non_ascii=True, extra_words=None):
    '''Create vocabulary from finrecord representations.'''
    text = " ".join(map(" ".join, session.query(RecordTypeRepr.value).all()))
    if remove_non_ascii:
        text = putil.remove_non_ascii(text)


    voc = set(map(str, find_ngrams(
        text, n = 1, min_len=2, remove_non_alphabetic=remove_non_alphabetic
    )))

    special_words = (
        "podstawowy", "obrotowy", "rozwodniony", "połączeń", "konsolidacji", 
        "należne", "wpłaty", "gazu", "ropy"
    )
    if remove_non_ascii:
        special_words = [putil.remove_non_ascii(word) for word in special_words]
    voc.update(special_words)

    if extra_words:
        text = " ".join(extra_words)
        if remove_non_ascii:
            text = putil.remove_non_ascii(text)
        voc.update(text.split(" "))

    return voc


def create_missing_records(records, company, fillrange):
    if not records: 
        return []

    min_date = min(record.timestamp for record in records)
    max_date = max(record.timestamp for record in records)
    if min_date == max_date: 
        return []

    if fillrange < 1: fillrange = 3
    dates = list(utils.datesrange(min_date, max_date, fillrange))
    records_by_rtype = utils.group_objects(records, key=lambda x: x.rtype_id)

    new_records = list()
    for rtype_id, records in records_by_rtype.items():
        records_timestamps = [record.timestamp for record in records]
        new_timestamps = set(dates) - set(records_timestamps)
        new_records.extend(
            Record(
                value=None, rtype_id=rtype_id, company_id=company.id, 
                timerange=fillrange, timestamp=timestamp
            )
            for timestamp in new_timestamps
        )

    return new_records