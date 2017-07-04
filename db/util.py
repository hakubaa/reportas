import itertools
from datetime import datetime
from concurrent import futures
import warnings

import requests
from sqlalchemy.exc import IntegrityError
from bs4 import BeautifulSoup

from db.models import (
	Report, RecordType, RecordTypeRepr, Record, Company, CompanyRepr
)
from parser.nlp import find_ngrams
import parser.util as putil


def upload_companies(session, data):
	'''Update companies in db.'''
	for item in data:
		try:
			instance = Company.get_or_create(
				session, defaults=item, isin=item.get("isin", item.get("ISIN"))
			)
		except KeyError:
			warnings.warn(
				"Record without ISIN number. Name: '{}'".
					format(item.get("name", None))
			)
			continue
		if instance.id:
			for key, value in item.items():
				setattr(instance, key, value)	
		else:
			session.add(instance)


def upload_report(session, doc, bls=True, nls=True, cfs=True,
	              override=False):
	'''Upload report to db.'''
	company = session.query(Company).filter_by(isin=doc.company["isin"]).one()

	if override: # override previous data
		report = session.query(Report).filter_by(
			timestamp=doc.timestamp, timerange=doc.timerange, company=company
		).first()
		if report:
			session.delete(report)
			session.commit()

	report = Report.create(
		session, timestamp=doc.timestamp, timerange=doc.timerange,
		company=company
	)

	# collect data for uploading
	data = []
	if bls: data.append({"items": doc.bls.items(), "names": doc.bls.names})
	if nls: data.append({"items": doc.nls.items(), "names": doc.nls.names})
	if cfs: data.append({"items": doc.cfs.items(), "names": doc.cfs.names})

	for record in data:
		# get names of columns and convert to more convinent form
		colnames = list(itertools.starmap( 
			lambda tr, ts: {        
				"timerange": tr, 
				"timestamp": datetime(ts[0], ts[1], ts[2])
			}, 
			record["names"]
		))
		for key, values in record["items"]:
			if len(values) != len(colnames): # skip incomplete records
				warnings.warn(
					"Different number of values and names for '{}' in "
					"'{!r}'".format(key, doc)
				)
				continue

			rtype = RecordType.get_or_create(session, name=key)

			for metadata, value in zip(colnames, values):
				Record.create_or_update(
					session, rtype=rtype, value=value, 
					timestamp=metadata["timestamp"], 
					timerange=metadata["timerange"], 
					report=report, company=company, override=override
				)

	return report


def upload_records_spec(session, spec):
	'''
	Create RecordType & RecordTypeRepr records in db in accordance with 
	specification.
	'''
	try: # ensure spec is iterable
		iter(spec)
	except TypeError:
		spec = [spec]

	for record_spec in spec:
		rtype = RecordType.get_or_create(
			session, name=record_spec["name"],
			statement=record_spec.get("statement", None)
		)
		for repr_spec in record_spec.get("repr", list()):
			repr_spec["rtype"] = rtype
			rtype_repr = RecordTypeRepr.create(session, **repr_spec)


def get_records_reprs(session, statement, lang="PL", n=1, min_len=2, 
                         remove_non_alphabetic=True):
    '''Get list of items representations for selected statement.'''
    spec = list()
    records = session.query(RecordTypeRepr).join(RecordType).\
                  filter(RecordType.statement.ilike(statement), 
                         RecordTypeRepr.lang.ilike(lang)
                  ).all()
    for record in records:
        nigrams = find_ngrams(
            putil.remove_non_ascii(record.value), n=n, min_len=min_len,
            remove_non_alphabetic=remove_non_alphabetic
        )
        spec.append(dict(id=record.rtype.name, ngrams=nigrams))

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