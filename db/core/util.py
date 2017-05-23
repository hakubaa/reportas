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
    valid_fields = model.__mapper__.columns.keys() +\
                   model.__mapper__.relationships.keys()

    params = dict(
        (k, v) for k, v in kwargs.items() 
        if not isinstance(v, ClauseElement) and k in valid_fields
    )
    if defaults: # filter defaults
        defaults = dict(
            (k, v) for k, v in defaults.items() if k in valid_fields
        )
    params.update(defaults or {})
    instance = model(**params)
    session.add(instance)
    return instance