__all__ = [ "dbmd" ]

from flask_admin import Admin

from app import db
from app.dbmd import views
from app.models import DBRequest, User
from db import models


dbmd = Admin(
    index_view=views.IndexView(template="admin/index.html", url="/dbmd"),
    template_mode="bootstrap3"
)

dbmd.add_view(views.CompanyView(models.Company, db.session))
dbmd.add_view(views.RecordTypeView(models.RecordType, db.session))
dbmd.add_view(views.RecordView(models.Record, db.session))
dbmd.add_view(views.ReportView(models.Report, db.session))
dbmd.add_view(views.UserView(User, db.session, endpoint="dbmd_user"))
dbmd.add_view(views.DBRequestView(DBRequest, db.session))
dbmd.add_view(views.SectorView(models.Sector, db.session))
dbmd.add_view(
    views.FinancialStatementView(models.FinancialStatement, db.session)
)
dbmd.add_view(views.RecordFormulaView(models.RecordFormula, db.session))