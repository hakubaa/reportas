import json

from flask import abort, request, jsonify, url_for
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from flask_restful import Resource

from app import db
from app.rapi import api, schemas
from app.rapi.util import (
    apply_query_parameters, MultipleObjectMixin, SingleObjectMixin, 
    ListResource, DetailResource
)
from db.models import Company, RecordType, RecordTypeRepr, Record, Report


class Root(Resource):

    def get(self):
        return {
            "companies": url_for("rapi.company_list"),
            "rtypes": url_for("rapi.rtype_list"),
            "reports": url_for("rapi.report_list"),
            "records": url_for("rapi.record_list")
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
        data = request.get_json()
        for key, value in data.items():
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


class CompanyRecordList(SingleObjectMixin, ListResource):
    model = Company
    schema = schemas.record
    collection = "records"

    def update_request_data(self, data, many, id):
        if many:
            for item in data:
                item["company"] = id
        else:
            data["company"] = id
        return data


class CompanyRecordDetail(DetailResource):
    schema = schemas.record

    def get_object(self, id, rid):
        try:
            obj = db.session.query(Record).join(Company).\
                    filter(Company.id == id, Record.id == rid).one()
        except NoResultFound:
            abort(404, "Record not found.") 
        else:
            return obj


class CompanyReportList(SingleObjectMixin, ListResource):
    model = Company
    schema = schemas.report
    collection = "reports"

    def update_request_data(self, data, many, id):
        if many:
            for item in data:
                item["company"] = id
        else:
            data["company"] = id
        return data


class RecordList(MultipleObjectMixin, ListResource):
    model = Record
    schema = schemas.record


class RecordDetail(SingleObjectMixin, DetailResource):
    model = Record
    schema = schemas.record


class ReportList(MultipleObjectMixin, ListResource):
    model = Report
    schema = schemas.report


class ReportDetail(SingleObjectMixin, DetailResource):
    model = Report
    schema = schemas.report


class ReportRecordList(SingleObjectMixin, ListResource):
    model = Report
    schema = schemas.record
    collection = "records"

    def update_request_data(self, data, many, id):
        if many:
            for item in data:
                item["report"] = id
        else:
            data["report"] = id
        return data


class ReportRecordDetail(DetailResource):
    schema = schemas.record

    def get_object(self, id, rid):
        try:
            obj = db.session.query(Record).join(Report).\
                    filter(Company.id == id, Report.id == rid).one()
        except NoResultFound:
            abort(404, "Record not found.") 
        else:
            return obj