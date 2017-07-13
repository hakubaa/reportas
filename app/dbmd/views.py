from db import models
from app import db
from app.dbmd import dbmd
from app.dbmd.base import AdminIndexView, ModelView, DBRequestMixin
from app.models import DBRequest, User


class CompanyView(DBRequestMixin, ModelView):
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


class DBRequestView(ModelView):
    pass


dbmd.add_view(
    CompanyView(models.Company, db.session)
)

dbmd.add_view(
    DBRequestView(DBRequest, db.session)
)