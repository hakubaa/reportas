from sqlalchemy.sql.expression import ClauseElement

      
def get_or_create(session, model, defaults=None, **kwargs):
    '''Return object if exists or create new one.'''
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance, False
    else:
        return create(session, model, defaults, **kwargs), True
        

def create_instance(model, **kwargs):
    '''Create instace of the model.'''
    valid_fields = model.__mapper__.columns.keys() +\
                   model.__mapper__.relationships.keys()

    params = dict(
        (k, v) for k, v in kwargs.items() 
        if not isinstance(v, ClauseElement) and k in valid_fields
    )

    return model(**params) 
        

def create(session, model, defaults=None, **kwargs):
    '''Create object and add it to db.'''
    kwargs.update(defaults or {})
    instance = create_instance(model, **kwargs)
    session.add(instance)
    return instance