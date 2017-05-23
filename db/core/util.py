from sqlalchemy.sql.expression import ClauseElement


def get_or_create(session, model, defaults=None, **kwargs):
    '''Return object if exists or create new one.'''
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        return create(session, model, defaults, **kwargs), True
        
        
def create(session, model, defaults=None, **kwargs):
    '''Create object.'''
    params = dict(
        (k, v) for k, v in kwargs.iteritems() 
        if not isinstance(v, ClauseElement)
    )
    params.update(defaults or {})
    instance = model(**params)
    session.add(instance)
    return instance