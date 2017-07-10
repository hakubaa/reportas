from app.dbmd import dbmd
from app import db
from app.dbmd.base import AdminIndexView, ModelView, DBRequestMixin
from db import models
from app.models import DBRequest, User


class CompanyView(DBRequestMixin, ModelView):
    column_searchable_list = ["name", "ticker", "fullname", "sector"]
    column_filters = ["sector", "debut"]
    column_list = (
        "isin", "name", "webpage", "ticker", "sector", "debut", "fullname"
    )
    column_labels = dict(fullname="Full Name")


class DBRequestView(ModelView):
    pass


dbmd.add_view(
    CompanyView(models.Company, db.session)
)

dbmd.add_view(
    DBRequestView(DBRequest, db.session)
)