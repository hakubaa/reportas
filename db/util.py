from db.models import FinRecordType, FinRecordTypeRepr
from parser.nlp import find_ngrams
from parser.util import remove_non_ascii


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