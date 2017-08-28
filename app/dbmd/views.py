from datetime import date

from flask import flash, url_for
from flask_admin import base as admin_base
from flask_admin.contrib import sqla
from flask_admin.contrib.sqla.filters import FilterInList, FilterEqual
from flask_admin.actions import action
from flask_login import current_user
from flask_admin.model import typefmt
from flask_admin.form.upload import FileUploadField
from wtforms.fields import TextAreaField, StringField, SelectField
from flask_admin.contrib.sqla.view import func

from flask_admin.model.form import InlineFormAdmin
from flask_admin.form.rules import BaseRule
from markupsafe import Markup

from db import models, records_factory
from app.dbmd.base import DBRequestMixin, PermissionRequiredMixin
from app.models import Permission, DBRequest
from app import db

#-------------------------------------------------------------------------------
# BUILDING BLOCKS FOR VIEWS
#-------------------------------------------------------------------------------

class Link(BaseRule):
    def __init__(self, endpoint, attribute, text):
        super(Link, self).__init__()
        self.endpoint = endpoint
        self.text = text
        self.attribute = attribute

    def __call__(self, form, form_opts=None, field_args={}):

        obj_id = getattr(form._obj, self.attribute, None)

        if obj_id:

            return Markup("""
            <div class='form-group'>
                <label class="col-md-2 control-label">
                    URL
                </label>    
                <div class='col-md-10'>
                    <p class='form-control-static'><a href='{url}'>{text}</a></p>
                </div>
            </div>
            """.format(
                obj_id=obj_id, url=url_for(self.endpoint, id=obj_id), 
                text=self.text
            ))


class MultiLink(BaseRule):
    def __init__(self, endpoint, relation, attribute):
        super(MultiLink, self).__init__()
        self.endpoint = endpoint
        self.relation = relation
        self.attribute = attribute

    def __call__(self, form, form_opts=None, field_args={}):
        _hrefs = []
        _objects = getattr(form._obj, self.relation)
        for _obj in _objects:
            _id = getattr(_obj, self.attribute, None)
            _link = '<a href="{url}">Edit {text}</a>'.format(
                url=url_for(self.endpoint, id=_id), text=str(_obj)
            )
            _hrefs.append(_link)

        return Markup('<br>'.join(_hrefs))


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
    can_set_page_size = True
    details_modal = True


def get_default_repr(view, context, model, name):
    try:
        default_repr = next(filter(lambda item: item.default, model.reprs))
    except StopIteration:
        if len(model.reprs) > 0:
            return model.reprs[0].value
        else:
            return None
    return default_repr.value


#-------------------------------------------------------------------------------

#-------------------------------------------------------------------------------
# VIEWS
#-------------------------------------------------------------------------------

class RecordFormulaView(DBRequestBasedView):
    column_list = ("rtype", "formula")
    column_filters = ["rtype.name"]
    column_labels = {"rtype": "Record Type", "rtype.name": "Record Type"}
    can_view_details = False
    column_formatters = {
        "default_repr": get_default_repr,
        "formula": lambda v, c, m, n: m.lhs_repr()
    }

    form_excluded_columns = ("version",)

    inline_models = [
        (
            models.FormulaComponent, 
            dict(
                form_columns=["rtype", "sign", "id"], form_label="Component",
                form_overrides=dict(sign=SelectField),
                form_args = dict(
                    sign=dict(
                        choices=[
                            ("1", "plus ( + )"),
                            ("-1", "minus ( - )")
                        ]
                    )
                ),
                column_labels=dict(rtype="Record Type")
            )
        )
    ]

    def modify_data(self, data):
        if "rtype" in data:
            data["rtype_id"] = getattr(data["rtype"], "id", None)
            del data["rtype"]
        if "components" in data:
            data["components"] = [
                { 
                    "rtype_id": getattr(comp["rtype"], "id", None), 
                    "sign": comp["sign"]
                }
                for comp in data["components"]
            ]
            
        return data


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
    column_labels = {"fullname": "Full Name", "sector.name": "Sector"}
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
        "rtype.name", "company.name", "timerange", "timestamp", "rtype.ftype.name",
        "synthetic"
    ]
    column_list = (
        "rtype",  "company", "timerange", "timestamp", "value"
    )
    column_labels = {
        "rtype": "Record Type", "rtype.name": "Record Type",
        "company.name": "Company Name", "rtype.ftype.name": "Financial Statement"
    }
    can_export = True

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
            dict(
                form_columns=["value", "lang", "id"], 
                form_label="Representation"
            )
        )
    ]

    can_view_details = False

    column_searchable_list = ["name"]
    column_filters = (
        "ftype.name",
        FilterEqual(
            models.RecordType.timeframe, "Time Frame", 
            options=(("pit", "Point-in-time"), ("pot", "Period-of-time"))
        )
    )
    column_list = ("name", "timeframe", "ftype", "default_repr")
    column_labels = {
        "ftype": "Financial Statement", 
        "ftype.name": "Financial Statement",
        "default_repr": "Default Repr.",
        "timeframe": "Time Frame"
    }
    column_formatters = {
        "default_repr": get_default_repr,
        "timeframe": lambda v, c, m, n: dict(
                            pit= "Point-in-time", pot="Period-of-time"
                        )[m.timeframe]
    }

    form_excluded_columns = ("version", "records", "formulas", "revformulas")
    form_overrides = dict(timeframe=SelectField)
    form_args = dict(
        timeframe=dict(
            choices=[
                ("pit", "Point-in-time"),
                ("pot", "Period-of-time")
            ]
        )
    )

    def modify_data(self, data):
        if "ftype" in data:
            data["ftype_id"] = getattr(data["ftype"], "id", None)
            del data["ftype"]
        return data


class FinancialStatementTypeView(DBRequestBasedView):
    inline_models = [
        (
            models.FinancialStatementTypeRepr,
            dict(
                form_columns=["value", "id", "default", "lang"], 
                form_label="Representation"
            )
        )
    ]

    can_view_details = False

    column_searchable_list = ["name"]
    column_list = ("name", "default_repr")
    column_formatters = dict(default_repr=get_default_repr)
    column_labels = dict(default_repr="Default Repr.")
    form_excluded_columns = ("version", "records", "rtypes")


class ReportView(DBRequestBasedView):
    inline_models = [
        (
            models.Record,
            dict(
                form_columns=[
                    "id", "value", "timerange", "timestamp", "rtype"
                ], 
                form_label="Record"
            )
        )
    ]
    
    can_view_details = False

    column_filters = [
        "timerange", "timestamp", "company.name", "company.ticker"
    ]
    column_list = ["company", "timerange", "timestamp", "consolidated"]
    column_labels = {
        "company.name": "Company Name", "company.ticker": "Company Ticker"
    }

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



class SubrequestModelForm(InlineFormAdmin):
    form_columns=["id", "model", "data", "action", "moderator_action", "errors"]
    form_label="Subrequest"

    form_rules = (
        "model", "data", "action", "moderator_action", "errors",
        Link(endpoint="dbrequest.edit_view", attribute="id", text="Edit Request")
    )


class DBRequestView(PermissionRequiredMixin, sqla.ModelView):
    create_view_permissions = Permission.ADMINISTER
    edit_view_permissions = Permission.ADMINISTER
    delete_view_permissions = Permission.ADMINISTER
    index_view_permissions = Permission.BROWSE_REQUESTS
    details_view_permissions = Permission.BROWSE_REQUESTS
    action_view_permissions = Permission.EXECUTE_REQUESTS

    can_view_details = True
    details_modal = True
    can_set_page_size = True

    column_list = ("user", "model", "action", "timestamp", "moderator_action", "outcome")
    column_filters = ("user", "model", "action", "moderator_action")

    list_template = "admin/model/dbrequest_list.html"

    inline_models = (SubrequestModelForm(DBRequest),)

    @action("accept", "Accept")
    def accept_requests(self, ids):
        successes_counter = 0
        requests_counter = 0

        new_records = list()
        for request_id in ids:
            request = db.session.query(DBRequest).get(request_id)
            if request:
                records_factory.session = db.session
                result = request.execute(current_user, records_factory)
                requests_counter += self._count_requests(result)
                successes_counter += self._count_successful_requests(result)
                new_records.extend(self._extract_records(result))

        synthetic_records = list()
        if len(new_records) > 0:
            synthetic_records = models.Record.create_synthetic_records(
                db.session, new_records
            )
        db.session.commit()

        msg = "%d of %d requests have been successfuly executed."
        if successes_counter < requests_counter:
            msg += " The errors can be view in details of the requests."
        flash(msg % (successes_counter, requests_counter))
        
        if len(synthetic_records) > 0:
            msg = "%d synthetic records have been created."
            flash(msg % len(synthetic_records))

    def _count_requests(self, result):
        counter = sum(
            self._count_requests(request) 
            for request in result["subrequests"]
        ) + 1
        return counter

    def _count_successful_requests(self, result):   
        counter = sum(
            self._count_successful_requests(request) 
            for request in result["subrequests"] 
        ) + (0 if result["errors"] else 1)
        return counter

    def _extract_records(self, result):
        records = list()
        if isinstance(result["instance"], models.Record):
            records.append(result["instance"])
        for subrequest in result["subrequests"]:
            records.extend(self._extract_records(subrequest))
        return records

    def get_query(self):
        # Return only main requests, ommit subrequests
        return self.session.query(self.model)\
                   .filter(self.model.parent_request == None)

    def get_count_query(self):
        return self.session.query(func.count('*'))\
                  .filter(self.model.parent_request == None)

class UserView(PermissionRequiredMixin, sqla.ModelView):
    default_permissions = Permission.ADMINISTER

    can_view_details = True
    details_modal = True

#-------------------------------------------------------------------------------