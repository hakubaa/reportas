from marshmallow_sqlalchemy import field_for
from marshmallow import validates, ValidationError, fields, pre_load
from sqlalchemy import exists

from app import ma, db
from app.rapi import api
from db.models import (
    Company, CompanyRepr, RecordType, RecordTypeRepr, Record, Report
)


class CompanyReprSchema(ma.ModelSchema):
    class Meta:
        model = CompanyRepr
        fields = ("id", "value", "company")

    # company = field_for(
    #     Company, "company", required=True,
    #     error_messages={"required": "Company is required."}
    # )   

#     @validates("company")
#     def validate_company(self, value):
#         (ret, ), = db.session.query(exists().where(Company.id == value.id))
#         if not ret:
#             raise ValidationError(
#                 "Company with id '{}' does not exist.".format(value.id)
#             )
#         return True

        
class CompanySchema(ma.ModelSchema):
    class Meta:
        model = Company
    reprs = fields.Nested(
        CompanyReprSchema, only=("id", "value"), many=True
    )
    records = ma.Hyperlinks(
        ma.URLFor("rapi.company_record_list", id="<id>")
    )
    # reports = ma.Hyperlinks(
    #     ma.URLFor("rapi.company_report_list", id="<id>")
    # )
    name = field_for(
        Company, "name", required=True,
        error_messages={"required": "Name is required."}
    )
    isin = field_for(
        Company, "isin", required=True,
        error_messages={"required": "ISIN is required."}
    )

    # @validates("isin")
    # def validate_isin(self, value):
    #     (ret, ), = db.session.query(exists().where(Company.isin == value))
    #     if ret:
    #         raise ValidationError("ISIN not unique")
    #     return True


class CompanySimpleSchema(ma.ModelSchema):
    class Meta:
        model = Company
        fields = ("id", "isin", "name", "ticker", "uri", "fullname")
    uri = ma.Hyperlinks(ma.URLFor("rapi.company_detail", id='<id>'))


class RecordTypeSchema(ma.ModelSchema):
    class Meta:
        model = RecordType
    name = field_for(
        RecordType, "name", required=True,
        error_messages={"required": "Name is required."}
    )
    statement = field_for(
        RecordType, "statement", required=True,
        error_messages={"required": "Statement is required."}
    )
    # reprs = ma.Hyperlinks(ma.URLFor("rapi.rtype_repr_list", id='<id>'))


class RecordTypeSimpleSchema(ma.ModelSchema):
    class Meta:
        model = RecordType
        fields = ("id", "name", "statement", "uri")
    uri = ma.Hyperlinks(ma.URLFor("rapi.rtype_detail", id='<id>'))


class RecordTypeReprSchema(ma.ModelSchema):
    class Meta:
        model = RecordTypeRepr
        fields = ("id", "value", "lang")


class RecordSchema(ma.ModelSchema):
    class Meta:
        model = Record

    # rtypes = fields.Nested(
    #     RecordTypeSchema, only=("id", "name", "statement"), many=False
    # )
    rtype = field_for(
        Record, "rtype", required=True,
        error_messages={"required": "RecordType is required."}
    )
    company = field_for(
        Record, "company", required=True,
        error_messages={"required": "Company is required."}
    )   

#     @validates("company")
#     def validate_company(self, value):
#         (ret, ), = db.session.query(exists().where(Company.id == value.id))
#         if not ret:
#             raise ValidationError(
#                 "Company with id '{}' does not exist.".format(value.id)
#             )
#         return True

#     @validates("rtype")
#     def validate_rtype(self, value):
#         (ret, ), = db.session.query(exists().where(RecordType.id == value.id))
#         if not ret:
#             raise ValidationError(
#                 "RecordType with id '{}' does not exist.".format(value.id)
#             )
#         return True


class ReportSchema(ma.ModelSchema):
    class Meta:
        model = Report
    records = ma.Hyperlinks(
        ma.URLFor("rapi.report_record_list", id="<id>")
    )


# company = CompanySchema()
# company_simple = CompanySimpleSchema()
# companyrepr = CompanyReprSchema()
# rtype = RecordTypeSchema()
# rtype_simple = RecordTypeSimpleSchema()
# rtyperepr = RecordTypeReprSchema()
# record = RecordSchema()
# report = ReportSchema()