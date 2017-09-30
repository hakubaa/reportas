from flask import render_template, url_for, redirect
from flask_login import login_required
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import func

from app import db
from app.analytics import analytics
from app.models import Permission
from app.decorators import permission_required

from db.models import Company


@analytics.route("/")
@login_required
def index():
    companies = db.session.query(Company).all()
    return render_template("analytics/index.html", companies=companies)


@analytics.route("/<company_name>")
@login_required
def ccar(company_name):
    try:
        company = db.session.query(Company).filter(
            func.lower(Company.name) == func.lower(company_name)
        ).one()
    except NoResultFound:
        return redirect(url_for("analytics.index"))
    else:
        return render_template("analytics/ccar.html", company=company)

    
# @analytics.route("/")
# @login_required
# def index():
#     return render_template("analytics/index.html")