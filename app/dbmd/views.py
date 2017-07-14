from flask_admin import base as admin_base
from flask_admin.contrib import sqla

from db import models
from app.dbmd.base import DBRequestMixin, PermissionRequiredMixin
from app.models import Permission

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

class CompanyView(DBRequestBasedView):
    inline_models = [
        (
            models.CompanyRepr, 
            dict(form_columns=["value", "id"], form_label="Representation")
        )
    ]
    
    column_searchable_list = ["name", "ticker", "fullname", "sector"]
    column_filters = ["sector", "debut"]
    column_list = (
        "isin", "name", "webpage", "ticker", "sector", "debut", "fullname"
    )
    column_labels = dict(fullname="Full Name")
    form_excluded_columns = ("version", "reports", "records")


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


class RecordView(DBRequestBasedView):
    form_excluded_columns = ("version",)

    
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
    column_list = ["company", "rtype", "timerange", "timestamp", "value"]
    form_excluded_columns = ("version")
    

class DBRequestView(PermissionRequiredMixin, sqla.ModelView):
    create_view_permissions = Permission.ADMINISTER
    edit_view_permissions = Permission.ADMINISTER
    delete_view_permissions = Permission.ADMINISTER
    index_view_permissions = Permission.BROWSE_REQUESTS
    details_view_permissions = Permission.BROWSE_REQUESTS

    can_view_details = True
    details_modal = True

    column_list = ("user", "model", "action", "timestamp", "moderator_action")
    column_filters = ("user", "model", "action", "moderator_action")


class UserView(PermissionRequiredMixin, sqla.ModelView):
    default_permissions = Permission.ADMINISTER

    can_view_details = True
    details_modal = True

#-------------------------------------------------------------------------------