from datetime import date

from flask import flash
from flask_admin import base as admin_base
from flask_admin.contrib import sqla
from flask_admin.actions import action
from flask_login import current_user
from flask_admin.model import typefmt
from flask_admin.form.upload import FileUploadField
from wtforms.fields import TextAreaField, StringField

from db import models, records_factory
from app.dbmd.base import DBRequestMixin, PermissionRequiredMixin
from app.models import Permission, DBRequest
from app import db

#-------------------------------------------------------------------------------
# BUILDING BLOCKS FOR VIEWS
#-------------------------------------------------------------------------------

class SpecificPermissionMixin(PermissionRequiredMixin):
    create_view_permissions = Permission.CREATE_REQUESTS
    edit_view_permissions = Permission.CREATE_REQUESTS
    delete_view_permissions = Permission.CREATE_REQUESTS
    index_view_permissions = Permission.BROWSE_DATA
    details_view_permissions = Permission.BROWSE_DATA


class IndexView(SpecificPermissionMixin, admin_base.AdminIndexView):
    pass
    

class DBRequestBasedView(
    SpecificPermissionMixin, DBRequestMixin, sqla.ModelView
):
    can_view_details = True
    details_modal = True

#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# VIEWS
#-------------------------------------------------------------------------------

class SectorView(DBRequestBasedView):
    form_excluded_columns = ("version",)
    column_searchable_list = ["name"]
    column_filters = ["name"]
    column_list = ("name",)
    can_view_details = False

    def modify_data(self, data):
        if "companies" in data:
            data["companies"] = [ company.id for company in data["companies"] ]
        return data


class CompanyView(DBRequestBasedView):
    inline_models = [
        (
            models.CompanyRepr, 
            dict(form_columns=["value", "id"], form_label="Representation")
        )
    ]
    
    column_searchable_list = ["name", "ticker", "fullname", "sector.name"]
    column_filters = ["debut", "sector.name"]
    column_list = (
        "isin", "name", "webpage", "ticker", "debut", "fullname", "sector"
    )
    column_labels = dict(fullname="Full Name")
    form_excluded_columns = ("version", "reports", "records")

    def modify_data(self, data):
        if "sector" in data:
            data["sector_id"] = getattr(data["sector"], "id", None)
            del data["sector"]
        return data


class RecordView(DBRequestBasedView):
    form_excluded_columns = ("version", "synthetic")

    column_searchable_list = ["company.name", "rtype.name"]
    column_filters = [
        "rtype.name", "rtype.statement", "company.name", 
        "timerange", "timestamp"
    ]
    column_list = (
        "rtype",  "company", "timerange", "timestamp", "value"
    )
    column_labels = dict(rtype="Record Type")

    def modify_data(self, data):
        if "rtype" in data:
            data["rtype_id"] = getattr(data["rtype"], "id", None)
            del data["rtype"]

        if "company" in data:
            data["company_id"] = getattr(data["company"], "id", None)
            del data["company"]

        if "report" in data:
            data["report_id"] = getattr(data["report"], "id", None)
            del data["report"]
            
        return data


class RecordTypeView(DBRequestBasedView):
    inline_models = [
        (
            models.RecordTypeRepr,
            dict(form_columns=["value", "id"], form_label="Representation")
        )
    ]

    can_view_details = False

    column_searchable_list = ["name"]
    column_filters = ["statement"]
    column_list = ("name", "statement")
    form_excluded_columns = ("version", "records", "formulas", "revformulas")

    
class ReportView(DBRequestBasedView):
    inline_models = [
        (
            models.Record,
            dict(
                form_columns=[
                    "id", "value", "timerange", "timestamp", "rtype", "company"
                ], 
                form_label="Record"
            )
        )
    ]
    
    can_view_details = False

    column_filters = ["timerange", "timestamp", "company"]
    column_list = ["company", "timerange", "timestamp", "consolidated"]

    form_args = dict(file=dict(validators=[]))
    form_columns = ["company", "timestamp", "timerange", "consolidated"]
    form_excluded_columns = ("version")
    form_overrides = dict(file=FileUploadField)

    form_widget_args = {
        "file": {
           "class": " "
        }
    }

    def modify_data(self, data):
        if "company" in data:
            data["company_id"] = getattr(data["company"], "id", None)
            del data["company"]

        if "records" in data:
            for record in data["records"]:
                if "company" in record:
                    record["company_id"] = getattr(record["company"], "id", None)
                    del record["company"]

                if "rtype" in record:
                    record["rtype_id"] = getattr(record["rtype"], "id", None)
                    del record["rtype"]
        return data

    def on_model_change(self, form, model, is_created):
        pass


class DBRequestView(PermissionRequiredMixin, sqla.ModelView):
    create_view_permissions = Permission.ADMINISTER
    edit_view_permissions = Permission.ADMINISTER
    delete_view_permissions = Permission.ADMINISTER
    index_view_permissions = Permission.BROWSE_REQUESTS
    details_view_permissions = Permission.BROWSE_REQUESTS
    action_view_permissions = Permission.EXECUTE_REQUESTS

    can_view_details = True
    details_modal = True

    column_list = ("user", "model", "action", "timestamp", "moderator_action", "outcome")
    column_filters = ("user", "model", "action", "moderator_action")

    list_template = "admin/model/dbrequest_list.html"

    @action("accept", "Accept")
    def accept_requests(self, ids):
        successes_counter = 0
        requests_counter = 0

        for request_id in ids:
            request = db.session.query(DBRequest).get(request_id)
            if request:
                records_factory.session = db.session
                results = request.execute(current_user, records_factory)
                requests_counter += len(results)
                successes_counter += sum(1 for _, error in results if not error)

        db.session.commit()
        msg = "%d of %d requests have been successfuly executed."
        if successes_counter < successes_counter:
            msg += " The errors can be view in details of the requests."
        flash(msg % (successes_counter, successes_counter))


class UserView(PermissionRequiredMixin, sqla.ModelView):
    default_permissions = Permission.ADMINISTER

    can_view_details = True
    details_modal = True

#-------------------------------------------------------------------------------