import itertools
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from db.models import FinReport, FinRecordType, FinRecordTypeRepr, FinRecord
from parser.nlp import find_ngrams
from parser.util import remove_non_ascii


def upload_record(db, **kwargs):
	'''Upload record to db.'''
	pass
	

def upload_report(db, doc, bls=True, nls=True, cfs=True,
	              update_records=True):
	'''Upload report to db.'''
	report = FinReport(timestamp=doc.timestamp, timerange=doc.timerange)
	db.session.add(report)
	db.session.commit()

	records_to_upload = list()
	if bls: # upload records from balance sheet
		# get names of columns and convert to more convinent form
		colnames = list(itertools.starmap( 
			lambda tr, ts: {        
				"timerange": tr, 
				"timestamp": datetime(ts[0], ts[1], ts[2])
			}, 
			doc.bls.names
		))
		for key, values in doc.bls.items():
			# find the record type in db
			try:
				rtype = db.session.query(FinRecordType).filter_by(name=key).one()
			except Exception: # finish it later
				raise

			if len(values) != len(colnames): # finish it later
				raise RuntimeException("different number of values and names")

			for metadata, value in zip(colnames, values):
				record = FinRecord(
					rtype, value, timestamp=metadata["timestamp"], 
					timerange=metadata["timerange"], report=report
				)
				try:
					db.session.add(record)
					db.session.commit()
				except IntegrityError:
					import pdb; pdb.set_trace()
				# records_to_upload.append(record)

	# db.session.bulk_save_objects(records_to_upload)
	db.session.commit()
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
		rtype = FinRecordType.create(**record_spec)
		db.session.add(rtype)
		for repr_spec in record_spec.get("repr", list()):
			rtype_repr = FinRecordTypeRepr.create(rtype=rtype, **repr_spec)
			db.session.add(rtype_repr)
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