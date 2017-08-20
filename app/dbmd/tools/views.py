from flask import url_for, redirect, flash, render_template
from flask_login import current_user, login_required

from app.dbmd.tools import dbmd_tools
from app.dbmd.tools import forms
from app.dbmd.tools.utils import *
from app.models import Permission
from app.decorators import permission_required
from app import db


@dbmd_tools.route("/miner", methods=("GET", "POST"))
@login_required
@permission_required(Permission.CREATE_REQUESTS)
def miner_index():
    return render_miner_index()


@dbmd_tools.route("/miner/pdf_file", methods=("POST",))
@login_required
@permission_required(Permission.CREATE_REQUESTS)
def pdf_file_miner():
    form = forms.ReportUploaderForm()
    if form.validate_on_submit():
        return render_pdf_file_miner(form, db.session)
    return render_miner_index(pdf_file_form=form)


@dbmd_tools.route("/miner/direct_input", methods=("POST",))
@login_required
@permission_required(Permission.CREATE_REQUESTS)
def direct_input_miner():
    form = forms.DirectInputForm()
    if form.validate_on_submit():
        return render_direct_input_miner(form, db.session)
    return render_miner_index(direct_input_form=form)


@dbmd_tools.route("/batch", methods=("GET",))
@login_required
@permission_required(Permission.CREATE_REQUESTS)
def batch_index():
    return render_batch_index()


@dbmd_tools.route("/batch/input", methods=("POST",))
@login_required
@permission_required(Permission.CREATE_REQUESTS)
def batch_uploader():
    form = forms.BatchUploaderForm()
    if form.validate_on_submit():
        return render_batch_uploader(form, db.session)
    return render_batch_index()


@dbmd_tools.route("/miner/upload_data", methods=("POST",))
@login_required
@permission_required(Permission.CREATE_REQUESTS)
def upload_data():
    data = convert_empty_strings_to_none(get_request_data(dict()))
    dbrequest = create_dbrequest(data, current_user)
    db.session.add(dbrequest)
    db.session.commit()
    flash("Request for uploading data has been registered. "
          "Please wait for its acceptance");
    return redirect(url_for("admin.index"))