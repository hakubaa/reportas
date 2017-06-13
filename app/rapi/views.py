import json

from flask import abort, request, jsonify
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource

from app import db
from app.rapi import api
from app.rapi import schemas
from db.models import Company


class RootAPI(Resource):

    def get(self):
        return {
            "companies": api.url_for(CompaniesListAPI)
        }


class CompaniesListAPI(Resource):

    def get(self):
        companies = db.session.query(Company).all()
        dump_data = schemas.company_simple.dump(companies, many=True).data
        return dump_data

    def post(self):
        obj, errors = schemas.company.load(request.form)
        if errors:
            return errors, 400
     
        db.session.add(obj)
        db.session.commit()
        return "", 201


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


class CompanyReprsListAPI(Resource):

    def get(self, id):
        try:
            company = db.session.query(Company).filter_by(id=id).one()
        except NoResultFound:
            abort(404, "Company not found.")



api.add_resource(RootAPI, "/", endpoint="root")
api.add_resource(CompaniesListAPI, "/companies", endpoint="company_list")
api.add_resource(CompanyAPI, "/companies/<int:id>", endpoint="company")
api.add_resource(CompanyReprsListAPI, "/companies/<int:id>/reprs", 
                 endpoint="crepr_list")