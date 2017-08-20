__all__ = [ 
    "FinancialReportDB", "render_miner_index", "get_request_data", 
    "create_dbrequest", "render_pdf_file_miner",
    "render_direct_input_miner", "convert_empty_strings_to_none",
    "render_batch_index", "render_batch_uploader"
]

import io
import os
import json
from datetime import datetime

from flask import render_template, request, current_app
import sqlalchemy
from dateutil.parser import parse

from app import db
from app.models import DBRequest
from db import models, serializers
from db.tools import get_records_reprs, get_companies_reprs
from rparser.core import FinancialReport, PDFFileIO, FinancialStatement

from .forms import ReportUploaderForm, DirectInputForm, BatchUploaderForm


#-------------------------------------------------------------------------------
# HELPER CLASSES
#-------------------------------------------------------------------------------

class FinancialReportDB(FinancialReport):
    def __init__(self, *args, session, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session
            
    def get_bls_spec(self):
        return self._get_records_reprs("bls")
    
    def get_ics_spec(self):
        return self._get_records_reprs("ics")
    
    def get_cfs_spec(self):
        return self._get_records_reprs("cfs")
        
    def get_companies_spec(self):
        return get_companies_reprs(self.session)

    def _get_records_reprs(self, name):
        return get_records_reprs(self.session, ftype=self._get_ftype(name))

    def _get_ftype(self, name):
        ftype = self.session.query(models.FinancialStatementType).\
                    filter_by(name=name).one()        
        return ftype

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
    ftype_query = session.query(models.FinancialStatementType)
    if spec_name in ("bls", None):
        ftype = ftype_query.filter_by(name="bls").one()    
        spec.extend(get_records_reprs(session, ftype))
    if spec_name in ("ics", None):
        ftype = ftype_query.filter_by(name="ics").one() 
        spec.extend(get_records_reprs(session, ftype))
    if spec_name in ("cfs", None):
        ftype = ftype_query.filter_by(name="cfs").one()  
        spec.extend(get_records_reprs(session, ftype))
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


def convert_empty_strings_to_none(data):
    data = dict(data)
    for key, item in data.items():
        if isinstance(item, str) and (item.isspace() or item == ""):
            data[key] = None
    return data


def create_dbrequest(data, user):
    records = None
    if "records" in data:
        records = data["records"]
        del data["records"]

    request = create_main_request(data, user)
    subrequests = create_record_subrequests(records, user)
    for subrequest in subrequests:
        request.add_subrequest(subrequest)

    return request


def create_main_request(data, user):
    if validate_data_for_report(data):
        main_request = create_report_main_request(data, user)
    else:
        main_request = create_wrapping_request(user)
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


def validate_data_for_report(data):
    required_fields = ("timerange", "timestamp", "company_id")
    if not set(required_fields) <= set(data.keys()):
        return False

    validators = [
        validate_date(data["timestamp"]),
        validate_integer(data["timerange"]),
        validate_integer(data["company_id"])
    ]

    if not all(validators):
        return False

    return True


def validate_date(timestamp):
    try:
        parse(timestamp)
    except (ValueError, TypeError):
        return False
    return True


def validate_integer(num):
    try:
        int(num)
    except (ValueError, TypeError):
        return False
    return True


def create_wrapping_request(user):
    dbrequest = DBRequest(action="create", user = user, wrapping_request=True)    
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
    try:
        report = db.session.query(models.Report).filter(
            models.Report.timerange == timerange,
            models.Report.timestamp == timestamp,
            models.Report.company_id == company_id
        ).first()
    except sqlalchemy.exc.DataError:
        return None
    return report


def render_batch_index(form=None):
    if not form:
        form = BatchUploaderForm()
    return render_template("admin/tools/batch_index.html", form=form)


def render_batch_uploader(form, session):
    rtypes = get_record_types(session)
    companies = session.query(models.Company.id, models.Company.name).all()

    report_timerange = form.data["report_timerange"]
    if report_timerange:
        report_timerange = int(report_timerange)

    report_timestamp = form.data["report_timestamp"]

    fschema_db = form.data["fschema"]
    formulas = session.query(models.RecordFormula).all()
    fschema = {
        "repr": fschema_db.default_repr.value,
        "rtypes": sorted(fschema_db.get_rtypes(), 
                         key=lambda item: item["position"]),
        "formulas": create_formulas_mapping(formulas),
        "calculable": [ 
            assoc.rtype.name for assoc in fschema_db.rtypes if assoc.calculable 
        ]
    }

    return render_template(
        "admin/tools/batch_uploader.html", company=form.data["company"], 
        rtypes=rtypes, companies=companies, fschema=fschema,
        report_timerange=report_timerange, report_timestamp=report_timestamp,
        
    )


def create_formulas_mapping(formulas_db):
    formulas = [ convert_db_formula(formula) for formula in formulas_db ]
    formulas_mapping = dict(base_rtypes=list())
    for formula in formulas:
        formulas_mapping["base_rtypes"].append(formula["rtype"])
        formulas_mapping.setdefault(formula["rtype"], []).append(formula)
        for component in formula["components"]:
            formulas_mapping.setdefault(component["rtype"], []).append(formula)
    return formulas_mapping


def convert_db_formula(db_formula):
    formula = dict(rtype=db_formula.rtype.name, components=list())
    for item in db_formula.rhs:
        formula["components"].append(dict(rtype=item.rtype.name, sign=item.sign))
    return formula