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
from app.rapi import schemas
from app.rapi.base import DetailView, ListView
from app.rapi import util as rutil


class ReportListView(ListView):
    model = models.Report
    schema = schemas.ReportSchema


class ReportDetailView(DetailView):
    model = models.Report
    schema = schemas.ReportSchema


class CompanyListView(ListView):
    model = models.Company
    schema = schemas.CompanySimpleSchema
    schema_post = schemas.CompanySchema


class CompanyDetailView(DetailView):
    model = models.Company
    schema = schemas.CompanySchema


class RecordListView(ListView):
    model = models.Record
    schema = schemas.RecordSchema


class RecordDetailView(DetailView):
    model = models.Record
    schema = schemas.RecordSchema


class RecordTypeListView(ListView):
    model = models.RecordType
    schema = schemas.RecordTypeSimpleSchema
    schema_post = schemas.RecordTypeSchema
    

class RecordTypeDetailView(DetailView):
    model = models.RecordType
    schema = schemas.RecordTypeSchema


class RecordTypeReprListView(ListView):
    model = models.RecordTypeRepr
    schema = schemas.RecordTypeReprSchema

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
    schema = schemas.RecordTypeReprSchema

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
    schema = schemas.RecordFormulaSchema
    
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
    schema = schemas.RecordFormulaSchema

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
    schema = schemas.FormulaComponentSchema
    
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
    schema = schemas.FormulaComponentSchema

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
    schema = schemas.RecordSchema

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
    schema = schemas.RecordSchema

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
    schema = schemas.CompanyReprSchema

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
    schema = schemas.CompanyReprSchema

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
    schema = schemas.ReportSchema

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
    schema = schemas.ReportSchema

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
    schema = schemas.RecordSchema

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
    schema = schemas.RecordSchema

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



@rapi.route("/")
@auth.login_required
@permission_required(Permission.READ_DATA)
def root():
    return jsonify({
        "companies": url_for("rapi.company_list"),
        "reports": url_for("rapi.report_list"),
        "records": url_for("rapi.record_list"),
        "rtypes": url_for("rapi.rtype_list")
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


def view_parse_text():
    text =  request.data.decode()
    if not text:
        abort(400, "No data send with request")
    
    encoding = request.content_encoding or "utf-8"
    try:
        text = text.decode(encoding)
    except AttributeError:
        pass

    spec_name = request.args.get("spec", "").lower()
    if spec_name not in ("", "bls", "nls", "cfs"):
        abort(400, "Unrecognized specification")

    data = rutil.parse_text(db.session, text, spec_name)

    return jsonify(data), 200  


def view_parse_file():
    file = request.files.get("file")
    if not (file and file.filename != ""):
        abort(400, "No file")

    filename = secure_filename(file.filename)
    if not rutil.allowed_file(filename):
        abort(400, "File not supported")

    # Save file to disc, it will be read by parser
    filepath = os.path.join(current_app.config.get("UPLOAD_FOLDER"), filename)
    file.save(filepath) 

    data = rutil.parse_file(filepath, db.session)

    return jsonify(data), 200


def view_parse_url():
    url = request.data.decode()
    if not url:
        abort(400, "No url send with request")

    filename = secure_filename(url.split("/")[-1])
    if not rutil.allowed_file(filename):
        abort(400, "File not supported")

    response = requests.get(url, stream=True)
    if response.status_code != 200:
        abort(400, "Unable to load file from given url")

    filepath = os.path.join(current_app.config.get("UPLOAD_FOLDER"), filename)
    with open(filepath, "wb") as f:
        for chunk in response:
            f.write(chunk)

    data = rutil.parse_file(filepath, db.session)   

    return jsonify(data), 200


@rapi.route("/parser", methods=["POST"])
@auth.login_required
def parser():
    data_type = request.args.get("type", "text")
    if data_type == "text":
        return view_parse_text()
    elif data_type == "url":
        return view_parse_url()
    elif data_type == "file":
        return view_parse_file()
    else:
        abort(400, "Unsupported type")


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


