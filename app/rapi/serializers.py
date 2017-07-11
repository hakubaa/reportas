'''
This module extends selected serializers defined in db.serializers with 
hyperlinks to related serializers.

The serializers that have been not extended, can also be imported through this 
module. That is the recommended practice for all modules in rapi blueprint.
'''

__all__ = [
    "CompanyReprSchema", "CompanySchema", "CompanySimpleSchema", 
    "RecordTypeSchema", "RecordTypeReprSchema", "RecordTypeSimpleSchema",
    "RecordSchema", "ReportSchema", "RecordFormulaSchema",
    "FormulaComponentSchema"
]

import werkzeug

from db.serializers import * # import all serializers
from app import ma


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


class CompanySchema(CompanySchema):
    records = ma.Hyperlinks(ma.URLFor("rapi.company_record_list", id="<id>"))
    reports = ma.Hyperlinks(ma.URLFor("rapi.company_report_list", id="<id>"))

class CompanySimpleSchema(CompanySimpleSchema):
    uri = ma.Hyperlinks(ma.URLFor("rapi.company_detail", id='<id>'))

class RecordTypeSchema(RecordTypeSchema):
    formulas = ma.Hyperlinks(ma.URLFor("rapi.rtype_formula_list", rid="<id>"))

class RecordTypeSimpleSchema(RecordTypeSimpleSchema):
    uri = ma.Hyperlinks(ma.URLFor("rapi.rtype_detail", id='<id>'))

class RecordSchema(RecordSchema):
    report = ma.Hyperlinks(URLFor("rapi.report_detail", id="<report_id>"))
    company = ma.Hyperlinks(URLFor("rapi.company_detail", id="<company_id>"))

class ReportSchema(ReportSchema):
    records = ma.Hyperlinks(ma.URLFor("rapi.report_record_list", id="<id>"))
    company = ma.Hyperlinks(URLFor("rapi.company_detail", id="<company_id>"))