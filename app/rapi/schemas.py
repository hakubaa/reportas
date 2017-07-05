__all__ = [
    "CompanyReprSchema", "CompanySchema", "CompanySimpleSchema", 
    "RecordTypeSchema", "RecordTypeReprSchema", "RecordTypeSimpleSchema",
    "RecordSchema", "ReportSchema", "RecordFormulaSchema",
    "FormulaComponentSchema"
]


from marshmallow_sqlalchemy import field_for
from marshmallow import (
    validates, ValidationError, fields, pre_load, validates_schema
)
from marshmallow.validate import OneOf
from sqlalchemy import exists, and_
import werkzeug

from app import ma, db
from app.rapi import api
import db.models as models
from db.models import (
    Company, CompanyRepr, RecordType, RecordTypeRepr, Record, Report,
    RecordFormula, FormulaComponent
)


class URLFor(ma.URLFor):
    '''Fix marshmallow URLFor to handle empty relationships.'''
    def __init__(self, *args, allow_null=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.allow_null = allow_null

    def _serialize(self, value, key, obj):
        try:
            return super()._serialize(value, key, obj)
        except werkzeug.routing.BuildError:
            if self.allow_null:
                return None
            else:
                raise


class CompanyReprSchema(ma.ModelSchema):
    class Meta:
        model = models.CompanyRepr
        fields = ("id", "value", "company_id")

    company_id = field_for(
        CompanyRepr, "company_id", required=True,
        error_messages={"required": "Company is required."}
    )   

    @validates("company_id")
    def validate_company(self, value):
        (ret, ), = db.session.query(exists().where(models.Company.id == value))
        if not ret:
            raise ValidationError(
                "Company with id '{}' does not exist.".format(value)
            )
        return True

        
class CompanySchema(ma.ModelSchema):
    class Meta:
        model = models.Company
        exclude = ("version",)

    reprs = fields.Nested(
        CompanyReprSchema, only=("id", "value"), many=True
    )
    records = ma.Hyperlinks(ma.URLFor("rapi.company_record_list", id="<id>"))
    reports = ma.Hyperlinks(ma.URLFor("rapi.company_report_list", id="<id>"))

    @validates("isin")
    def validate_isin(self, value):
        (ret, ), = db.session.query(
            exists().where(models.Company.isin == value)
        )
        if ret:
            raise ValidationError("ISIN not unique")
        return True


class CompanySimpleSchema(ma.ModelSchema):
    class Meta:
        model = Company
        fields = ("id", "isin", "name", "ticker", "uri", "fullname")

    uri = ma.Hyperlinks(ma.URLFor("rapi.company_detail", id='<id>'))


class RecordTypeReprSchema(ma.ModelSchema):
    class Meta:
        model = RecordTypeRepr
        fields = ("id", "value", "lang", "rtype_id")

    rtype_id = field_for(
        RecordTypeRepr, "rtype_id", required=True,
        error_messages={"required": "RecordType is required."}
    )   


class RecordTypeSchema(ma.ModelSchema):
    class Meta:
        model = RecordType
        exclude = ("records", "version", "revcomponents")

    formulas = ma.Hyperlinks(ma.URLFor("rapi.rtype_formula_list", rid="<id>"))

    statement = field_for(
        RecordType, "statement", required=True,
        error_messages={"required": "Statement is required."},
        validate=[OneOf(("bls", "nls", "cfs"))]
    )
    reprs = fields.Nested(
        RecordTypeReprSchema, only=("id", "value"), many=True
    )

    @validates("name")
    def validate_name(self, value):
        (ret,), = db.session.query(
            exists().where(models.RecordType.name == value)
        )
        if ret:
            raise ValidationError("name not unique")
        return True


class RecordTypeSimpleSchema(ma.ModelSchema):
    class Meta:
        model = RecordType
        fields = ("id", "name", "statement", "uri")

    uri = ma.Hyperlinks(ma.URLFor("rapi.rtype_detail", id='<id>'))


class RecordSchema(ma.ModelSchema):
    class Meta:
        model = Record
        exclude = ("version",)

    rtype = fields.Nested(
        RecordTypeSchema, only=("name", "statement"), many=False
    )
    timestamp = fields.DateTime("%Y-%m-%d", required=True)
    rtype_id = field_for(
        Record, "rtype_id", required=True,
        error_messages={"required": "RecordType is required."}
    )
    company_id = field_for(
        Record, "company_id", required=True,
        error_messages={"required": "Company is required."}
    )   
    report_id = field_for(Record, "report_id")   

    report = ma.Hyperlinks(URLFor("rapi.report_detail", id="<report_id>"))
    company = ma.Hyperlinks(URLFor("rapi.company_detail", id="<company_id>"))

    @validates("company_id")
    def validate_company(self, value):
        (ret, ), = db.session.query(exists().where(Company.id == value))
        if not ret:
            raise ValidationError(
                "Company with id '{}' does not exist.".format(value)
            )
        return True

    @validates("rtype_id")
    def validate_rtype(self, value):
        (ret, ), = db.session.query(exists().where(RecordType.id == value))
        if not ret:
            raise ValidationError(
                "RecordType with id '{}' does not exist.".format(value)
            )
        return True

    @validates("report_id")
    def validate_report(self, value):
        (ret, ), = db.session.query(exists().where(Report.id == value))
        if not ret:
            raise ValidationError(
                "Report with id '{}' does not exist.".format(value)
            )
        return True

    @validates_schema
    def validate_uniquness(self, data):
        if not ("timerange" in data and "timestamp" in data and 
                "company_id" in data and "rtype_id" in data):
            return False

        (ret, ), = db.session.query(exists().where(and_(
            Record.timerange == data["timerange"],
            Record.timestamp == data["timestamp"],
            Record.company_id == data["company_id"],
            Record.rtype_id == data["rtype_id"]
        )))
        if ret:
            raise ValidationError(
                "Record not unique in terms of timerange, timestamp, "
                "company and type.", field_names=("record")
            )
        return True


class ReportSchema(ma.ModelSchema):
    class Meta:
        model = Report
        exclude = ("version",)

    timestamp = fields.DateTime("%Y-%m-%d", required=True)
    records = ma.Hyperlinks(ma.URLFor("rapi.report_record_list", id="<id>"))
    company = ma.Hyperlinks(URLFor("rapi.company_detail", id="<company_id>"))


class FormulaComponentSchema(ma.ModelSchema):
    class Meta:
        model = FormulaComponent
        exclude = ("version",)
        
    formula_id = field_for(
        FormulaComponent, "formula_id", required=True,
        error_messages={"required": "Formula is required."}
    )   
    rtype_id = field_for(
        FormulaComponent, "rtype_id", required=True,
        error_messages={"required": "RecordType is required."}
    )
    
    rtype = fields.Nested(RecordTypeSchema, only=("name"), many=False)
    
    @validates("rtype_id")
    def validate_rtype(self, value):
        (ret, ), = db.session.query(exists().where(RecordType.id == value))
        if not ret:
            raise ValidationError(
                "RecordType with id '{}' does not exist.".format(value)
            )
        return True
        
    @validates("formula_id")
    def validate_formula(self, value):
        (ret, ), = db.session.query(exists().where(RecordFormula.id == value))
        if not ret:
            raise ValidationError(
                "RecordFormula with id '{}' does not exist.".format(value)
            )
        return True 
        
        
class RecordFormulaSchema(ma.ModelSchema):
    class Meta:
        model = RecordFormula
        fields = ("components", "id", "rtype_id")
        
    rtype_id = field_for(
        RecordFormula, "rtype_id", required=True,
        error_messages={"required": "RecordType is required."}
    )   
    
    components = fields.Nested(
        FormulaComponentSchema, only=("rtype", "sign", "rtype_id"), many=True
    )

    @validates("rtype_id")
    def validate_rtype(self, value):
        (ret, ), = db.session.query(exists().where(RecordType.id == value))
        if not ret:
            raise ValidationError(
                "RecordType with id '{}' does not exist.".format(value)
            )
        return True