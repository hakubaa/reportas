from db.models import FinRecordType, FinRecordTypeRepr


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