import itertools
import json
import os

from flask import (
    current_app, make_response, render_template, jsonify, request, g, abort,
    url_for
)
from flask.views import MethodView
from flask_login import current_user
from werkzeug.utils import secure_filename
import requests

from app import debugtoolbar, db
from app.models import DBRequest, Permission
from app.rapi import api, rapi
from app.user import auth
from app.user.auth import permission_required
import db.models as models
from app.rapi import serializers
from app.rapi.base import DetailView, ListView


class ReportListView(ListView):
    model = models.Report
    schema = serializers.ReportSchema


class ReportDetailView(DetailView):
    model = models.Report
    schema = serializers.ReportSchema


class CompanyListView(ListView):
    model = models.Company
    schema = serializers.CompanySimpleSchema
    schema_post = serializers.CompanySchema


class CompanyDetailView(DetailView):
    model = models.Company
    schema = serializers.CompanySchema


class RecordListView(ListView):
    model = models.Record
    schema = serializers.RecordSchema


class RecordDetailView(DetailView):
    model = models.Record
    schema = serializers.RecordSchema


class RecordTypeListView(ListView):
    model = models.RecordType
    schema = serializers.RecordTypeSimpleSchema
    schema_post = serializers.RecordTypeSchema
    

class RecordTypeDetailView(DetailView):
    model = models.RecordType
    schema = serializers.RecordTypeSchema


class RecordTypeReprListView(ListView):
    model = models.RecordTypeRepr
    schema = serializers.RecordTypeReprSchema

    def get_objects(self, id):
        rtype = db.session.query(models.RecordType).get(id)
        if not rtype:
            abort(404)
        return rtype.reprs

    def modify_data(self, data):
        data["rtype_id"] = data["id"]
        del data["id"]
        return data


class RecordTypeReprDetailView(DetailView):
    model = models.RecordTypeRepr
    schema = serializers.RecordTypeReprSchema

    def get_object(self, rid, id):
        rtype_repr = db.session.query(models.RecordTypeRepr).filter(
            models.RecordTypeRepr.rtype_id == rid,
            models.RecordTypeRepr.id == id
        ).first()
        if not rtype_repr:
            abort(404)
        return rtype_repr

    def modify_data(self, data):
        rtype_id = data["rid"]
        data["rtype_id"] = rtype_id
        del data["rid"]
        return data


class RecordFormulaListView(ListView):
    model = models.RecordFormula
    schema = serializers.RecordFormulaSchema
    
    def get_objects(self, rid):
        rtype = db.session.query(models.RecordType).get(rid)
        if not rtype:
            abort(404)
        return rtype.formulas
        
    def modify_data(self, data):
        data["rtype_id"] = data["rid"]
        del data["rid"]
        return data


class RecordFormulaDetailView(DetailView):
    model = models.RecordFormula
    schema = serializers.RecordFormulaSchema

    def get_object(self, rid, fid):
        formula = db.session.query(models.RecordFormula).filter(
            models.RecordFormula.rtype_id == rid,
            models.RecordFormula.id == fid
        ).first()
        if not formula:
            abort(404)
        return formula

    def modify_data(self, data):
        rtype_id = data["rid"]
        data["rtype_id"] = rtype_id
        data["id"] = data["fid"]
        del data["rid"]
        del data["fid"]
        return data


class FormulaComponentListView(ListView):
    model = models.FormulaComponent
    schema = serializers.FormulaComponentSchema
    
    def get_objects(self, rid, fid):
        formula = db.session.query(models.RecordFormula).filter(
            models.RecordFormula.rtype_id == rid,
            models.RecordFormula.id == fid
        ).first()
        if not formula:
            abort(404)
        return formula.components
        
    def modify_data(self, data):
        data["formula_id"] = data["fid"]
        del data["rid"]
        del data["fid"]
        return data 


class FormulaComponentDetailView(DetailView):
    model = models.FormulaComponent
    schema = serializers.FormulaComponentSchema

    def get_object(self, rid, fid, cid):
        component = db.session.query(self.model).filter(
            models.FormulaComponent.formula_id == fid,
            models.FormulaComponent.id == cid
        ).first()
        if not component:
            abort(404)
        return component

    def modify_data(self, data):
        data["formula_id"] = data["fid"]
        data["id"] = data["cid"]
        del data["rid"]
        del data["fid"]
        del data["cid"]
        return data


class CompanyRecordListView(ListView):
    model = models.Record
    schema = serializers.RecordSchema

    def get_objects(self, id):
        company = db.session.query(models.Company).get(id)
        if not company:
            abort(404)
        return company.records

    def modify_data(self, data):
        data["company_id"] = data["id"]
        del data["id"]
        return data


class CompanyRecordDetailView(DetailView):
    model = models.Record
    schema = serializers.RecordSchema

    def get_object(self, id, rid):
        record = db.session.query(models.Record).filter(
            models.Record.company_id == id,
            models.Record.id == rid
        ).first()
        if not record:
            abort(404)
        return record

    def modify_data(self, data):
        record_id = data["rid"]
        company_id = data["id"]
        data["company_id"] = company_id
        data["id"] = record_id
        del data["rid"]
        return data


class CompanyReprListView(ListView):
    model = models.CompanyRepr
    schema = serializers.CompanyReprSchema

    def get_objects(self, id):
        company = db.session.query(models.Company).get(id)
        if not company:
            abort(404)
        return company.reprs

    def modify_data(self, data):
        data["company_id"] = data["id"]
        del data["id"]
        return data


class CompanyReprDetailView(DetailView):
    model = models.CompanyRepr
    schema = serializers.CompanyReprSchema

    def get_object(self, id, rid):
        record = db.session.query(models.CompanyRepr).filter(
            models.CompanyRepr.company_id == id,
            models.CompanyRepr.id == rid
        ).first()
        if not record:
            abort(404)
        return record

    def modify_data(self, data):
        repr_id = data["rid"]
        company_id = data["id"]
        data["company_id"] = company_id
        data["id"] = repr_id
        del data["rid"]
        return data


class CompanyReportListView(ListView):
    model = models.Report
    schema = serializers.ReportSchema

    def get_objects(self, id):
        company = db.session.query(models.Company).get(id)
        if not company:
            abort(404)
        return company.reports

    def modify_data(self, data):
        data["company_id"] = data["id"]
        del data["id"]
        return data


class CompanyReportDetailView(DetailView):
    model = models.Report
    schema = serializers.ReportSchema

    def get_object(self, id, rid):
        record = db.session.query(models.Report).filter(
            models.Report.company_id == id,
            models.Report.id == rid
        ).first()
        if not record:
            abort(404)
        return record

    def modify_data(self, data):
        report_id = data["rid"]
        company_id = data["id"]
        data["company_id"] = company_id
        data["id"] = report_id
        del data["rid"]
        return data


class ReportRecordListView(ListView):
    model = models.Record
    schema = serializers.RecordSchema

    def get_objects(self, id):
        report = db.session.query(models.Report).get(id)
        if not report:
            abort(404)
        return report.records

    def modify_data(self, data):
        data["report_id"] = data["id"]
        del data["id"]
        return data


class ReportRecordDetailView(DetailView):
    model = models.Record
    schema = serializers.RecordSchema

    def get_object(self, id, rid):
        record = db.session.query(models.Record).filter(
            models.Record.report_id == id,
            models.Record.id == rid
        ).first()
        if not record:
            abort(404)
        return record

    def modify_data(self, data):
        report_id = data["id"]
        record_id = data["rid"]
        data["report_id"] = report_id
        data["id"] = record_id
        del data["rid"]
        return data


class FSchemaListView(ListView):
    model = models.FinancialStatementSchema
    schema = serializers.FinancialStatementSchemaSimple


class FSchemaDetailView(DetailView):
    model = models.FinancialStatementSchema
    schema = serializers.FinancialStatementSchema


class FSchemaRecordsView(ListView):
    model = None
    schema = serializers.RecordSchema

    def get_schema(self, *args, **kwargs):
        schema = self.schema(*args, **kwargs)
        return schema

    def get_fschema(self, id):
        fschema = db.session.query(models.FinancialStatementSchema).get(id)
        if not fschema:
            abort(404)
        return fschema

    def get_formated_data(self, fschema, company, timerange):
        records = fschema.get_records(company, timerange, db.session)
        return {
            "company": serializers.CompanySimpleSchema().dump(company).data,
            "timerange": timerange,
            "count": len(records),
            "schema": [
                {  
                    "position": item["position"],
                    "rtype": serializers.RecordTypeSchema(only=("id", "name")).\
                                 dump(item["rtype"]).data
                }
                for item in fschema.get_rtypes()
            ],
            "data": self._dump_records(
                fschema, records, self.get_schema(only=("id", "value"))
            )
        }

    def get_records(self, fschema, company, timerange):
        records = fschema.get_records(company, timerange, db.session)
        return {
            "count": len(records),
            "records": self.get_schema(only=(
                "id", "rtype", "rtype_id", "value", "timestamp", 
                "timerange", "company_id")
            ).dump(records, many=True).data
        }

    def create_response_body(self, fschema, company, timerange, format_data):
        if format_data in ("T", "TRUE", "Y", "YES"):
            data_method = self.get_formated_data
        else:
            data_method = self.get_records
        return data_method(fschema, company, timerange)

    @auth.login_required
    @permission_required(Permission.BROWSE_DATA)
    def get(self, id):
        fschema = self.get_fschema(id)
        company_id = request.args.get("company", None)
        timerange = request.args.get("timerange", 0)
        format_data = request.args.get("format", "F").upper()

        if company_id is None:
            abort(400)
        company = db.session.query(models.Company).get(company_id)

        return jsonify(self.create_response_body(
            fschema, company, timerange, format_data
        )), 200

    def _dump_records(self, fschema, records, record_schema):
        rtypes = fschema.get_rtypes()
        record_key = lambda x: x.timestamp
        grouped_records = itertools.groupby(
            sorted(records, key=record_key), key=record_key
        )
        output = [
            {
                "timestamp": timestamp,
                "records": [
                    { 
                        "record": record_schema.dump(record).data if record else None, 
                        "position": posrtype["position"],
                        # "rtype": posrtype["rtype"].name,
                        # "rtype_id": posrtype["rtype"].id
                    }
                    for record, posrtype in self._zip_by_keys(
                        records, rtypes, key1=lambda x: x.rtype, 
                        key2=lambda x: x["rtype"]
                    )
                ]
            }
            for timestamp, records in grouped_records
        ]
        return output 

    def _zip_by_keys(self, it1, it2, key1, key2):
        dict1 = { key1(item): item for item in it1 }
        dict2 = { key2(item): item for item in it2 }
        return (
            (dict1.get(key, None), dict2.get(key, None))
            for key in set(itertools.chain(dict1, dict2))
        )


@rapi.route("/")
@auth.login_required
@permission_required(Permission.BROWSE_DATA)
def root():
    return jsonify({
        "companies": url_for("rapi.company_list"),
        "reports": url_for("rapi.report_list"),
        "records": url_for("rapi.record_list"),
        "rtypes": url_for("rapi.rtype_list"),
        "fschemas": url_for("rapi.fschema_list")
    })

rapi.add_url_rule(
    "/companies",  
    view_func=CompanyListView.as_view("company_list")
)
rapi.add_url_rule(
    "/companies/<int:id>", 
    view_func=CompanyDetailView.as_view("company_detail")
)

rapi.add_url_rule(
    "/companies/<int:id>/reprs",
    view_func=CompanyReprListView.as_view("company_repr_list")
)
rapi.add_url_rule(
    "/companies/<int:id>/reprs/<int:rid>",
    view_func=CompanyReprDetailView.as_view("company_repr_detail")
)

rapi.add_url_rule(
    "/companies/<int:id>/records",
    view_func=CompanyRecordListView.as_view("company_record_list")
)
rapi.add_url_rule(
    "/companies/<int:id>/records/<int:rid>",
    view_func=CompanyRecordDetailView.as_view("company_record_detail")
)

rapi.add_url_rule(
    "/companies/<int:id>/reports",
    view_func=CompanyReportListView.as_view("company_report_list")
)
rapi.add_url_rule(
    "/companies/<int:id>/reports/<int:rid>",
    view_func=CompanyReportDetailView.as_view("company_report_detail")
)


rapi.add_url_rule("/rtypes",
                  view_func=RecordTypeListView.as_view("rtype_list"))
rapi.add_url_rule("/rtypes/<int:id>",
                  view_func=RecordTypeDetailView.as_view("rtype_detail"))

rapi.add_url_rule("/rtypes/<int:id>/reprs",
                  view_func=RecordTypeReprListView.as_view("rtype_repr_list"))
rapi.add_url_rule("/rtypes/<int:id>/reprs/<int:rid>",
                  view_func=RecordTypeReprDetailView.as_view("rtype_repr_detail"))

rapi.add_url_rule(
    "/rtypes/<int:rid>/formulas",
    view_func=RecordFormulaListView.as_view("rtype_formula_list")
)
rapi.add_url_rule(
    "/rtypes/<int:rid>/formulas/<int:fid>",
    view_func=RecordFormulaDetailView.as_view("rtype_formula_detail")
)

rapi.add_url_rule(
    "/rtypes/<int:rid>/formulas/<int:fid>/components",
    view_func=FormulaComponentListView.as_view("formula_component_list")
)
rapi.add_url_rule(
    "/rtypes/<int:rid>/formulas/<int:fid>/components/<int:cid>",
    view_func=FormulaComponentDetailView.as_view("formula_component_detail")
)


rapi.add_url_rule("/reports", view_func=ReportListView.as_view("report_list"))
rapi.add_url_rule("/reports/<int:id>", 
                  view_func=ReportDetailView.as_view("report_detail"))

rapi.add_url_rule("/reports/<int:id>/records",
                  view_func=ReportRecordListView.as_view("report_record_list"))
rapi.add_url_rule(
    "/reports/<int:id>/records/<int:rid>",
    view_func=ReportRecordDetailView.as_view("report_record_detail")
)

rapi.add_url_rule("/records", view_func=RecordListView.as_view("record_list"))
rapi.add_url_rule("/records/<int:id>", 
                  view_func=RecordDetailView.as_view("record_detail"))


rapi.add_url_rule("/fschemas", view_func=FSchemaListView.as_view("fschema_list"))
rapi.add_url_rule("/fschemas/<int:id>", 
                  view_func=FSchemaDetailView.as_view("fschema_detail"))
rapi.add_url_rule("/fschemas/<int:id>/records", methods=["GET"],
                  view_func=FSchemaRecordsView.as_view("fschema_records"))

# @rapi.after_request
# def after_request(response):
#     # Wrap JSON responses by HTML and ask flask-debugtoolbar to inject 
#     # own HTML into it
#     if (current_app.config.get("DEBUG_TB_ENABLED", False) 
#             and response.mimetype == "application/json" 
#             and response.status_code != 401
#     ):
#         # response.direct_passthrough = False
#         args = dict(response=response.data.decode("utf-8"), 
#                     http_code=response.status)
#         html_wrapped_response = make_response(
#             render_template("wrap_json.html", **args), response.status_code
#         )
#         # response = debugtoolbar.process_response(html_wrapped_response)
#         response = html_wrapped_response

#     return response


