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
from app.models import Permission
from app.user import auth
from app.user.auth import permission_required


# class Root(Resource):
#     decorators = [
#         auth.login_required
#     ]

#     def get(self):
#         return {
#             "companies": url_for("rapi.company_list"),
#             "rtypes": url_for("rapi.rtype_list"),
#             "reports": url_for("rapi.report_list"),
#             "records": url_for("rapi.record_list")
#         }


# class CompanyList(MultipleObjectMixin, ListResource):
#     model = Company
#     decorators = [
#         permission_required(Permission.UPLOAD_DATA),
#         auth.login_required
#     ]

#     def get_schema_cls(self):
#         if request.method == "GET":
#             return schemas.CompanySimpleSchema
#         else:
#             return schemas.CompanySchema


# class CompanyDetail(SingleObjectMixin, DetailResource):
#     model = Company
#     schema = schemas.CompanySchema
#     decorators = [
#         auth.login_required
#     ]

#     def put(self, id):
#         company = self.get_object(id)
#         data = request.get_json()
#         for key, value in data.items():
#             if key not in ("id", ):
#                 setattr(company, key, value)
#         try:
#             db.session.commit()
#         except IntegrityError:
#             abort(400, "ISIN not unique")


# class CompanyReprList(SingleObjectMixin, ListResource):
#     model = Company
#     schema = schemas.CompanyReprSchema
#     collection = "reprs"
#     decorators = [
#         auth.login_required
#     ]


# class RecordTypeList(MultipleObjectMixin, ListResource):
#     model = RecordType
#     decorators = [
#         auth.login_required
#     ]

#     def get_schema_cls(self):
#         if request.method == "GET":
#             return schemas.RecordTypeSimpleSchema
#         else:
#             return schemas.RecordTypeSchema


# class RecordTypeDetail(SingleObjectMixin, DetailResource):
#     model = RecordType
#     schema = schemas.RecordTypeSchema
#     decorators = [
#         auth.login_required
#     ]


# class RecordTypeReprList(SingleObjectMixin, ListResource):
#     model = RecordType
#     schema = schemas.RecordTypeReprSchema
#     collection = "reprs"
#     decorators = [
#         auth.login_required
#     ]


# class RecordTypeReprDetail(DetailResource):
#     schema = schemas.RecordTypeReprSchema
#     decorators = [
#         auth.login_required
#     ]

#     def get_object(self, id, rid):
#         try:
#             obj = db.session.query(RecordTypeRepr).join(RecordType).\
#                     filter(RecordType.id == id, RecordTypeRepr.id == rid).one()
#         except NoResultFound:
#             abort(404, "RecordTypeRepr not found.") 
#         else:
#             return obj


# class CompanyRecordList(SingleObjectMixin, ListResource):
#     model = Company
#     schema = schemas.RecordSchema
#     collection = "records"
#     decorators = [
#         auth.login_required
#     ]

#     def update_request_data(self, data, many, id):
#         if many:
#             for item in data:
#                 item["company"] = id
#         else:
#             data["company"] = id
#         return data


# class CompanyRecordDetail(DetailResource):
#     schema = schemas.RecordSchema
#     decorators = [
#         auth.login_required
#     ]

#     def get_object(self, id, rid):
#         try:
#             obj = db.session.query(Record).join(Company).\
#                     filter(Company.id == id, Record.id == rid).one()
#         except NoResultFound:
#             abort(404, "Record not found.") 
#         else:
#             return obj


# class CompanyReportList(SingleObjectMixin, ListResource):
#     model = Company
#     schema = schemas.ReportSchema
#     collection = "reports"
#     decorators = [
#         auth.login_required
#     ]

#     def update_request_data(self, data, many, id):
#         if many:
#             for item in data:
#                 item["company"] = id
#         else:
#             data["company"] = id
#         return data


# class RecordList(MultipleObjectMixin, ListResource):
#     model = Record
#     schema = schemas.RecordSchema
#     decorators = [
#         auth.login_required
#     ]

# class RecordDetail(SingleObjectMixin, DetailResource):
#     model = Record
#     schema = schemas.RecordSchema
#     decorators = [
#         auth.login_required
#     ]

# class ReportList(MultipleObjectMixin, ListResource):
#     model = Report
#     schema = schemas.ReportSchema
#     decorators = [
#         auth.login_required
#     ]

# class ReportDetail(SingleObjectMixin, DetailResource):
#     model = Report
#     schema = schemas.ReportSchema
#     decorators = [
#         auth.login_required
#     ]

# class ReportRecordList(SingleObjectMixin, ListResource):
#     model = Report
#     schema = schemas.RecordSchema
#     collection = "records"
#     decorators = [
#         auth.login_required
#     ]

#     def update_request_data(self, data, many, id):
#         if many:
#             for item in data:
#                 item["report"] = id
#         else:
#             data["report"] = id
#         return data


# class ReportRecordDetail(DetailResource):
#     schema = schemas.RecordSchema
#     decorators = [
#         auth.login_required
#     ]
    
#     def get_object(self, id, rid):
#         try:
#             obj = db.session.query(Record).join(Report).\
#                     filter(Company.id == id, Report.id == rid).one()
#         except NoResultFound:
#             abort(404, "Record not found.") 
#         else:
#             return obj