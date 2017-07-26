from copy import deepcopy
import json
import os
import io

from flask import (
    url_for, render_template, current_app, redirect, request, flash
)
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.dbmd.tools.forms import ReportUploaderForm
from app.dbmd.tools.util import (
    FinancialReportDB, read_report_from_file, get_company, get_record_types
)
from app.dbmd.tools import dbmd_tools
from app.models import File, Permission, DBRequest
from app.decorators import permission_required
from app import db
from db import models


@dbmd_tools.route("/report_uploader", methods=("GET", "POST"))
@login_required
@permission_required(Permission.CREATE_REQUESTS)
def report_uploader():
    form = ReportUploaderForm()
    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)
        path = os.path.join(current_app.config.get("UPLOAD_FOLDER"), filename)
        file.save(path)	
        file_db = File(name=filename, user=current_user)
        db.session.add(file_db)
        db.session.commit()
        return redirect(url_for("dbmd_tools.parser", filename=filename))

    return render_template("admin/tools/report_uploader.html", form=form)


@dbmd_tools.route("/parser", methods=("GET",))
@login_required
@permission_required(Permission.CREATE_REQUESTS)
def parser():
    filename = request.args.get("filename", None)
    if not filename:
        flash("File not selected.")
        return redirect(url_for("dbmd_tools.report_uploader"))

    path = os.path.join(current_app.config.get("UPLOAD_FOLDER"), filename)
    if not os.path.exists(path):
        flash("File does not exist. Please load the proper file first.")
        return redirect(url_for("dbmd_tools.report_uploader"))
    
    report = read_report_from_file(path, db.session)
    
    company = None
    if report.company and "isin" in report.company:
        company = get_company(report.company["isin"], db.session)
    
    rtypes = get_record_types(db.session)

    return render_template("admin/tools/parser.html", report=report, 
                           company=company, rtypes=rtypes)


@dbmd_tools.route("/parser", methods=("POST",))
@login_required
@permission_required(Permission.CREATE_REQUESTS)
def parser_post():
    data = get_request_data(dict())
    dbrequest = create_report_dbrequest(data)
    db.session.add(dbrequest)
    db.session.commit()
    return redirect(url_for("admin.index"))

def get_request_data(default=None):
    request_data = request.form["data"]
    if request_data:
        return json.loads(request_data)
    return default

def create_report_dbrequest(data):
    records = None
    if "records" in data:
        records = data["records"]
        del data["records"]

    main_request = create_report_main_request(data)
    subrequests = create_record_subrequests(records)
    for subrequest in subrequests:
        main_request.add_subrequest(subrequest)

    return main_request

def create_report_main_request(data):
    report = get_report(**data)
    if not report:
        action = "create"
        data = {
            key: value for key, value in data.items() 
            if key in ("timerange", "timestamp", "company_id", "consolidated") 
        }
    else:
        action = "update"
        data = dict(id=report.id)

    dbrequest = DBRequest(
        action=action, data=json.dumps(data), model="Report"
    )    
    return dbrequest

def create_record_subrequests(data):
    if not data:
        return list()

    subrequests = [
        DBRequest(action="create", data=json.dumps(record), model="Record")
        for record in data
    ]
    return subrequests

def get_report(timestamp=None, timerange=None, company_id=None, **kwargs):
    report = db.session.query(models.Report).filter(
        models.Report.timerange == timerange,
        models.Report.timestamp == timestamp,
        models.Report.company_id == company_id
    ).first()
    return report


@dbmd_tools.route("/parserek", methods=("GET",))
def parserek():
    return render_template("admin/tools/parserek.html")