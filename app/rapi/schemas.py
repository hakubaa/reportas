from marshmallow_sqlalchemy import field_for
from marshmallow import validates, ValidationError
from sqlalchemy import exists

from app import ma, db
from app.rapi import api
from db.models import Company, CompanyRepr, RecordType, RecordTypeRepr


class CompanySchema(ma.ModelSchema):
    class Meta:
        model = Company
    reprs = ma.List(ma.HyperlinkRelated("rapi.crepr_list"))
    name = field_for(
        Company, "name", required=True,
        error_messages={"required": "Name is required."}
    )
    isin = field_for(
        Company, "isin", required=True,
        error_messages={"required": "ISIN is required."}
    )

    @validates("isin")
    def validate_isin(self, value):
        (ret, ), = db.session.query(exists().where(Company.isin == value))
        if ret:
            raise ValidationError("ISIN not unique")
        return True


class CompanySimpleSchema(ma.ModelSchema):
    class Meta:
        model = Company
        fields = ("id", "isin", "name", "ticker", "uri", "fullname")
    uri = ma.Hyperlinks(ma.URLFor("rapi.company", id='<id>'))


class CompanyReprSchema(ma.ModelSchema):
    class Meta:
        model = CompanyRepr
        fields = ("id", "value")


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
    reprs = ma.Hyperlinks(ma.URLFor("rapi.rtype_repr_list", id='<id>'))


class RecordTypeSimpleSchema(ma.ModelSchema):
    class Meta:
        model = RecordType
        fields = ("id", "name", "statement", "uri")
    uri = ma.Hyperlinks(ma.URLFor("rapi.rtype", id='<id>'))


class RecordTypeReprSchema(ma.ModelSchema):
    class Meta:
        model = RecordTypeRepr
        fields = ("id", "value", "lang")


company = CompanySchema()
company_simple = CompanySimpleSchema()
companyrepr = CompanyReprSchema()
rtype = RecordTypeSchema()
rtype_simple = RecordTypeSimpleSchema()
rtyperepr = RecordTypeReprSchema()