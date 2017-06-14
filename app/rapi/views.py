import json

from flask import abort, request, jsonify
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource

from app import db
from app.rapi import api
from app.rapi import schemas
from db.models import Company, RecordType


class RootAPI(Resource):

    def get(self):
        return {
            "companies": api.url_for(CompanyListAPI),
            "rtypes": api.url_for(RecordTypeListAPI),
            # "reports":
            # "records":
        }


def create_list_api(name, cls, get_schema=None, post_schema=None):

    if not get_schema and not post_schema:
        raise RuntimeError("no schema defined")

    get_schema = get_schema or post_schema
    post_schema = post_schema or get_schema

    def get(self):
        objs = db.session.query(cls).all()
        data = get_schema.dump(objs, many=True).data
        return data

    def post(self):
        obj, errors = post_schema.load(request.form)
        if errors:
            return errors, 400

        db.session.add(obj)
        db.session.commit()
        return "", 201

    new_cls = type(name, (Resource,), {"get": get, "post": post})
    return new_cls


CompanyListAPI = create_list_api(
    "CompanyListAPI", Company, get_schema=schemas.company_simple,
    post_schema=schemas.company
)


class CompanyAPI(Resource):

    def _get_company(self, id):
        company = db.session.query(Company).get(id)
        if not company:
            abort(404, "Company not found.")
        return company

    def get(self, id):
        company = self._get_company(id)
        data = schemas.company.dump(company).data
        return data

    def delete(self, id):
        company = self._get_company(id)
        db.session.delete(company)
        db.session.commit()

    def put(self, id):
        company = self._get_company(id)
        for key, value in request.form.items():
            if key not in ("id", ):
                setattr(company, key, value)
        try:
            db.session.commit()
        except IntegrityError:
            abort(400, "ISIN not unique")


RecordTypeListAPI = create_list_api(
    "RecordTypeListAPI", RecordType, get_schema=schemas.rtype_simple,
    post_schema=schemas.rtype
)


class RecordTypeAPI(Resource):

    def _get_rtype(self, id):
        rtype = db.session.query(RecordType).get(id)
        if not rtype:
            abort(404, "RecordType not found.")
        return rtype

    def get(self, id):
        rtype = self._get_rtype(id)
        data = schemas.rtype.dump(rtype).data
        return data

    def delete(self, id):
        rtype = self._get_rtype(id)
        db.session.delete(rtype)
        db.session.commit()

    def put(self, id):
        rtype = self._get_rtype(id)
        for key, value in request.form.items():
            if key not in ("id", ):
                setattr(rtype, key, value)
        db.session.commit()
        

class CompanyReprListAPI(Resource):

    def get(self, id):
        try:
            company = db.session.query(Company).filter_by(id=id).one()
        except NoResultFound:
            abort(404, "Company not found.")


api.add_resource(RootAPI, "/", endpoint="root")
api.add_resource(CompanyListAPI, "/companies", endpoint="company_list")
api.add_resource(CompanyAPI, "/companies/<int:id>", endpoint="company")
api.add_resource(CompanyReprListAPI, "/companies/<int:id>/reprs", 
                 endpoint="crepr_list")
api.add_resource(RecordTypeListAPI, "/rtypes", endpoint="rtype_list")
api.add_resource(RecordTypeAPI, "/rtypes/<int:id>", endpoint="rtype")