import json

from flask import abort, request, jsonify
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource

from app import db
from app.rapi import api
from app.rapi import schemas
from db.models import Company, RecordType, RecordTypeRepr


class RootAPI(Resource):

    def get(self):
        return {
            "companies": api.url_for(CompanyListAPI),
            "rtypes": api.url_for(RecordTypeListAPI),
            # "reports":
            # "records":
        }


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
        objs = db.session.query(self.model).all()
        return objs


class ListResource(Resource):
    schema = None
    collection = None

    def get_schema(self):
        return self.schema

    def get(self, *args, **kwargs):
        obj = self.get_object(*args, **kwargs)
        if self.collection:
            obj = getattr(obj, self.collection)
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


class CompanyListAPI(MultipleObjectMixin, ListResource):
    model = Company

    def get_schema(self):
        if request.method == "GET":
            return schemas.company_simple
        else:
            return schemas.company


class CompanyAPI(SingleObjectMixin, DetailResource):
    model = Company
    schema = schemas.company

    def put(self, id):
        company = self.get_object(id)
        for key, value in request.form.items():
            if key not in ("id", ):
                setattr(company, key, value)
        try:
            db.session.commit()
        except IntegrityError:
            abort(400, "ISIN not unique")


class CompanyReprListAPI(SingleObjectMixin, ListResource):
    model = Company
    schema = schemas.companyrepr
    collection = "reprs"


class RecordTypeListAPI(MultipleObjectMixin, ListResource):
    model = RecordType

    def get_schema(self):
        if request.method == "GET":
            return schemas.rtype_simple
        else:
            return schemas.rtype


class RecordTypeAPI(SingleObjectMixin, DetailResource):
    model = RecordType
    schema = schemas.rtype


class RecordTypeReprListAPI(SingleObjectMixin, ListResource):
    model = RecordType
    schema = schemas.rtyperepr
    collection = "reprs"


class RecordTypeReprAPI(DetailResource):
    schema = schemas.rtyperepr

    def get_object(self, id, rid):
        try:
            obj = db.session.query(RecordTypeRepr).join(RecordType).\
                    filter(RecordType.id == id, RecordTypeRepr.id == rid).one()
        except NoResultFound:
            abort(404, "RecordTypeRepr not found.") 
        else:
            return obj



api.add_resource(RootAPI, "/", endpoint="root")
api.add_resource(CompanyListAPI, "/companies", endpoint="company_list")
api.add_resource(CompanyAPI, "/companies/<int:id>", endpoint="company")
api.add_resource(CompanyReprListAPI, "/companies/<int:id>/reprs", 
                 endpoint="crepr_list")
api.add_resource(RecordTypeListAPI, "/rtypes", endpoint="rtype_list")
api.add_resource(RecordTypeAPI, "/rtypes/<int:id>", endpoint="rtype")
api.add_resource(RecordTypeReprListAPI, "/rtypes/<int:id>/reprs",
                 endpoint="rtype_repr_list")
api.add_resource(RecordTypeReprAPI, "/rtypes/<int:id>/reprs/<int:rid>",
                 endpoint="rtype_repr")