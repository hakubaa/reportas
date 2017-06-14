from marshmallow_sqlalchemy import field_for
from marshmallow import validates, ValidationError
from sqlalchemy import exists

from app import ma, db
from app.rapi import api
from db.models import Company, CompanyRepr, RecordType


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
        fields = ("id", "isin", "name", "ticker", "uri")
        # dump_only = True
    uri = ma.Hyperlinks(ma.URLFor("rapi.company", id='<id>'))


class CompanyReprSchema(ma.ModelSchema):
    class Meta:
        model = CompanyRepr


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
    

class RecordTypeSimpleSchema(ma.ModelSchema):
    class Meta:
        model = RecordType
        fields = ("id", "name", "statement", "uri")
        # dump_only = True
    uri = ma.Hyperlinks(ma.URLFor("rapi.rtype", id='<id>'))



company = CompanySchema()
company_simple = CompanySimpleSchema()
companyrepr = CompanyReprSchema()
rtype = RecordTypeSchema()
rtype_simple = RecordTypeSimpleSchema()