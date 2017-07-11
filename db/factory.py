class DBRecordFactory():
    '''
    Factory for creating records in db. Use marshmallow schemas for creating 
    and updating objects.
    '''
    
    def __init__(self, session=None):
        self.session = session
        self.models = dict()
    
    def get_schema(self, model_cls):
        if isinstance(model_cls, str):
            for key, value in self.models.items():
                if key.__name__ == model_cls:
                    model_cls = key
                    schema = value
                    break
            else:
                schema = None
        else:
            schema = self.models.get(model_cls, None)

        if not schema:
            msg = "Schema for '{!r}' is not defined".format(model_cls.__name__)
            raise RuntimeError(msg)

        return schema

    def get_model(self, model_cls):
        for model in self.models.keys():
            if model.__name__ == model_cls:
                return model
        return None
    
    def create(self, model_cls, **kwargs):
        schema = self.get_schema(model_cls)()
        instance, errors = schema.load(data=kwargs, session=self.session)
        if not errors and instance:
            self.session.add(instance)
        return instance, errors
        
    def update(self, instance, **kwargs):
        schema = self.get_schema(instance.__class__)()
        instance, errors = schema.load(
            data=kwargs, instance=instance, partial=True, session=self.session
        )
        return instance, errors
    
    def register_model(self, model_cls, schema=None):
        self.models[model_cls] = schema

    def register_schema(self, model_cls=None):
        def decorator(schema_cls):
            nonlocal model_cls
            if not model_cls:
                if hasattr(schema_cls, "Meta"):
                    model_cls = getattr(schema_cls.Meta, "model")
            self.register_model(model_cls, schema_cls)
            return schema_cls
        return decorator