from flask import render_template, abort, jsonify, request
from sqlalchemy.orm.exc import NoResultFound
import requests

from app import db
from app.main import main

from db.models import Company



from flask import current_app, make_response, render_template

from app import debugtoolbar



@main.route("/", methods=["GET"])
def index():
	return "<h1>REPORTAS</h1>"


@main.route("/companies", methods=["GET"])
def companies():
	data = db.session.query(Company).filter(Company.name != "").all()
	return render_template("main/companies.html", data=data)


@main.route("/companies/<isin>", methods=["GET"])
def company(isin):
	try:
		data = db.session.query(Company).filter_by(isin=isin).one()
	except NoResultFound:
		abort(404)
	else:
		return render_template("main/company.html", data=data)