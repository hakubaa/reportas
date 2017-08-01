__all__ = [ 
    "FinancialReportDB", "render_miner_index", "get_request_data", 
    "create_report_dbrequest", "render_pdf_file_miner",
    "render_direct_input_miner"
]

import io
import os
import json
from datetime import datetime

from flask import render_template, request, current_app

from app import db
from app.models import DBRequest
from db import models
from db.util import get_records_reprs, get_companies_reprs
from rparser.base import FinancialReport, PDFFileIO, FinancialStatement

from .forms import ReportUploaderForm, DirectInputForm


#-------------------------------------------------------------------------------
# HELPE CLASSES
#-------------------------------------------------------------------------------

class FinancialReportDB(FinancialReport):
    def __init__(self, *args, session, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session
            
    def get_bls_spec(self):
        return get_records_reprs(self.session, "bls")
    
    def get_ics_spec(self):
        return get_records_reprs(self.session, "ics")
    
    def get_cfs_spec(self):
        return get_records_reprs(self.session, "cfs")
        
    def get_companies_spec(self):
        return get_companies_reprs(self.session)


#-------------------------------------------------------------------------------
# HELPER FUNCTIONS
#-------------------------------------------------------------------------------

def render_miner_index(pdf_file_form=None, direct_input_form=None):
    return render_template(
        "admin/tools/miner_index.html", 
        pdf_file_form=pdf_file_form or ReportUploaderForm(),
        direct_input_form=direct_input_form or DirectInputForm()
    )    


def render_pdf_file_miner(form, session):
    file = convert_to_pdf_file(
        filename=form.get_filename() or "temp.pdf", 
        content=form.get_file()
    )
    report = FinancialReportDB(
        io.TextIOWrapper(file), session=session,
        timestamp=form.data["report_timestamp"] or None,
        timerange=form.data["report_timerange"] or None
    )

    company = form.data["company"]
    if not company and (report.company and "isin" in report.company):
        company = get_company(report.company["isin"], session)

    rtypes = get_record_types(session)
    companies = session.query(models.Company.id, models.Company.name).all()

    return render_template(
        "admin/tools/pdf_file_miner.html", report=report, 
        company=company, rtypes=rtypes, companies=companies
    )


def render_direct_input_miner(form, session):
    content = form.data["content"]
    spec = get_records_spec(session)
    rtypes = get_record_types(session)
    company = form.data["company"]
    companies = session.query(models.Company.id, models.Company.name).all()

    report_timerange = form.data["report_timerange"]
    if report_timerange:
        report_timerange = int(report_timerange)

    report_timestamp = form.data["report_timestamp"]

    data = FinancialStatement(
        content, spec, timerange=report_timerange, timestamp=report_timestamp
    )

    return render_template(
        "admin/tools/direct_input_miner.html", content=content.split("\n"),
        data=data, company=company, rtypes=rtypes, 
        report_timerange=report_timerange, report_timestamp=report_timestamp,
        companies=companies
    )


def get_records_spec(session, spec_name=None):
    spec = list()
    if spec_name in ("bls", None):
        spec.extend(get_records_reprs(session, "bls"))
    if spec_name in ("ics", None):
        spec.extend(get_records_reprs(session, "ics"))
    if spec_name in ("cfs", None):
        spec.extend(get_records_reprs(session, "cfs"))
    return spec


def convert_to_pdf_file(filename, content):
    path = os.path.join(current_app.config.get("UPLOAD_FOLDER"), filename)
    content.save(path)     
    return PDFFileIO(path)
        
        
def get_company(isin, session):
    company = session.query(models.Company).filter_by(isin=isin).first()  
    return company 


def get_record_types(session):
    rtypes = session.query(models.RecordType.id, models.RecordType.name).all()
    return [dict(zip(("id", "name"), rtype)) for rtype in rtypes]


def get_request_data(default=None):
    request_data = request.form["data"]
    if request_data:
        return json.loads(request_data)
    return default


def create_report_dbrequest(data, user):
    records = None
    if "records" in data:
        records = data["records"]
        del data["records"]

    main_request = create_report_main_request(data, user)
    subrequests = create_record_subrequests(records, user)
    for subrequest in subrequests:
        main_request.add_subrequest(subrequest)

    return main_request


def create_report_main_request(data, user):
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
        action=action, data=json.dumps(data), model="Report",
        user = user
    )    
    return dbrequest


def create_record_subrequests(data, user):
    if not data:
        return list()

    subrequests = [
        DBRequest(
            action="create", data=json.dumps(record), 
            model="Record", user=user
        )
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