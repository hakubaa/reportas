import itertools
from datetime import datetime
from concurrent import futures
import warnings

import requests
from sqlalchemy.exc import IntegrityError
from bs4 import BeautifulSoup

from db.models import (
	FinReport, FinRecordType, FinRecordTypeRepr, FinRecord, Company
)
from parser.nlp import find_ngrams
from parser.util import remove_non_ascii


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
		report = session.query(FinReport).filter_by(
			timestamp=doc.timestamp, timerange=doc.timerange, company=company
		).first()
		if report:
			session.delete(report)
			session.commit()

	report = FinReport.create(
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

			rtype = FinRecordType.get_or_create(session, name=key)

			for metadata, value in zip(colnames, values):
				FinRecord.create_or_update(
					session, rtype=rtype, value=value, 
					timestamp=metadata["timestamp"], 
					timerange=metadata["timerange"], 
					report=report, company=company, override=override
				)

	return report


def upload_finrecords_spec(db, spec, commit=True):
	'''
	Create FinRecordType & FinRecordTypeRepr records in db in accordance with 
	specification.
	'''
	try: # ensure spec is iterable
		iter(spec)
	except TypeError:
		spec = [spec]

	for record_spec in spec:
		rtype = FinRecordType.get_or_create(
			db.session, name=record_spec["name"],
			statement=record_spec.get("statement", None)
		)
		for repr_spec in record_spec.get("repr", list()):
			repr_spec["rtype"] = rtype
			rtype_repr = FinRecordTypeRepr.create(db.session, **repr_spec)
	if commit:
		db.session.commit()


def create_spec(db, statement, lang="PL", n=1, min_len=2, 
	            remove_non_alphabetic=True):
	'''Create specification for selected statement and language.'''
	spec = list()
	records = db.session.query(FinRecordTypeRepr).join(FinRecordType).\
	              filter(FinRecordType.statement == statement, 
	              	     FinRecordTypeRepr.lang == lang
	              ).all()
	for record in records:
		nigrams = find_ngrams(
			remove_non_ascii(record.value), n=n, min_len=min_len,
			remove_non_alphabetic=remove_non_alphabetic
		)
		spec.append(dict(id=record.rtype.name, ngrams=nigrams))

	return spec