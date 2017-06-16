import json

from flask import abort, request, jsonify
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource

from app import db
from app.rapi import api, schemas
from app.rapi.util import (
    apply_query_parameters, MultipleObjectMixin, SingleObjectMixin, 
    ListResource, DetailResource
)
from db.models import Company, RecordType, RecordTypeRepr


class Root(Resource):

    def get(self):
        return {
            "companies": api.url_for(CompanyListAPI),
            "rtypes": api.url_for(RecordTypeListAPI),
            # "reports":
            # "records":
        }


class CompanyList(MultipleObjectMixin, ListResource):
    model = Company

    def get_schema(self):
        if request.method == "GET":
            return schemas.company_simple
        else:
            return schemas.company


class CompanyDetail(SingleObjectMixin, DetailResource):
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


class CompanyReprList(SingleObjectMixin, ListResource):
    model = Company
    schema = schemas.companyrepr
    collection = "reprs"


class RecordTypeList(MultipleObjectMixin, ListResource):
    model = RecordType

    def get_schema(self):
        if request.method == "GET":
            return schemas.rtype_simple
        else:
            return schemas.rtype


class RecordTypeDetail(SingleObjectMixin, DetailResource):
    model = RecordType
    schema = schemas.rtype


class RecordTypeReprList(SingleObjectMixin, ListResource):
    model = RecordType
    schema = schemas.rtyperepr
    collection = "reprs"


class RecordTypeReprDetail(DetailResource):
    schema = schemas.rtyperepr

    def get_object(self, id, rid):
        try:
            obj = db.session.query(RecordTypeRepr).join(RecordType).\
                    filter(RecordType.id == id, RecordTypeRepr.id == rid).one()
        except NoResultFound:
            abort(404, "RecordTypeRepr not found.") 
        else:
            return obj