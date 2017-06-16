from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource
from flask import request, abort

from app import db


def apply_query_parameters(query):
    limit = request.args.get("limit")
    offset = request.args.get("offset")
    query = query.limit(limit).offset(offset)

    sort = request.args.get("sort")
    if sort:
        sort = "".join(sort.split()) # remove all whitespaces
        for field in sort.split(","):
            index = 1 if field.startswith("-") else 0
            try:
                model = query.column_descriptions[0]["type"]
                column = model.__table__.columns[field[index:]]
                if index:
                    column = column.desc()
            except KeyError:
                continue
            else:
                query = query.order_by(column)   
    return query


class SingleObjectMixin:
    model = None

    def get_object(self, id):
        cls_name = self.model.__class__.__name__
        obj = db.session.query(self.model).get(id)
        if not obj:
            abort(404, "{} not found.".format(cls_name))
        return obj


class MultipleObjectMixin:
    model = None

    def get_object(self, *args, **kwargs):
        query = db.session.query(self.model)
        objs = apply_query_parameters(query).all()
        return objs


class ListResource(Resource):
    schema = None
    collection = None

    def get_schema(self):
        return self.schema

    def get(self, *args, **kwargs):
        obj = self.get_object(*args, **kwargs)
        if self.collection:
            query = getattr(obj, self.collection)
            obj = apply_query_parameters(query).all()
        schema = self.get_schema()
        data = schema.dump(obj, many=True).data
        return {
            "results": data,
            "count": len(data)
        }

    def post(self, *args, **kwargs):
        parent_obj = None
        if args or kwargs:
            parent_obj = self.get_object(*args, **kwargs)

        schema = self.get_schema()
        obj, errors = schema.load(request.form)
        if errors:
            return {
                "errors": errors
            }, 400

        if parent_obj:
            getattr(parent_obj, self.collection).append(obj)
        else:
            db.session.add(obj)
        db.session.commit()
        return "", 201


class DetailResource(Resource):
    schema = None

    def get_schema(self):
        return self.schema

    def get(self, *args, **kwargs):
        obj = self.get_object(*args, **kwargs)
        data = self.get_schema().dump(obj).data
        return data

    def delete(self, *args, **kwargs):
        obj = self.get_object(*args, **kwargs)
        db.session.delete(obj)
        db.session.commit()

    def put(self, *args, **kwargs):
        obj = self.get_object(*args, **kwargs)
        for key, value in request.form.items():
            if key not in ("id", ):
                setattr(obj, key, value)
        db.session.commit()