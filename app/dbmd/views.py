from flask import abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app import db
from app.dbmd.forms import CompanyForm
from app.dbmd import dbmd
from app.user import auth
from db.models import Company


@dbmd.route("/companies", methods=["GET", "POST"])
@auth.login_required
def list_companies():
    companies = db.session.query(Company).all()
    return render_template(
        "dbmd/companies/companies.html",
         companies=companies, title="Departments"
    )