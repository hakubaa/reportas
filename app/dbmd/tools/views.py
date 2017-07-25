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
from app.models import File, Permission
from app.decorators import permission_required
from app import db


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


@dbmd_tools.route("/parser", methods=("GET", "POST"))
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


@dbmd_tools.route("/parserek", methods=("GET",))
def parserek():
    return render_template("admin/tools/parserek.html")