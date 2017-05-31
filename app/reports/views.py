import os

from flask import (
	request, redirect, url_for, current_app, render_template, flash, abort
)
from werkzeug.utils import secure_filename
import requests
from sqlalchemy.orm.exc import NoResultFound

from app import db
from app.models import File
from app.reports import reports
from db.models import Company
from db.util import get_companies_reprs, get_finrecords_reprs, create_vocabulary

from parser.models import FinancialReport


def allowed_file(filename):
	exts = current_app.config.get("ALLOWED_EXTENSIONS")
	return "." in filename and filename.rsplit(".", 1)[1].lower() in exts
			

@reports.route("/", methods=["GET"])
def index():
	return "<h3>Upload Report</h3>"


@reports.route("/load", methods=["GET", "POST"])
def load_report():
	if request.method == "POST":

		file = request.files.get("file")
		if file and file.filename != "":
			filename = secure_filename(file.filename)

			if not allowed_file(filename):
				flash("Not allowed extension")
				return redirect(request.url)

			path = os.path.join(current_app.config.get("UPLOAD_FOLDER"), 
				                filename)
			file.save(path)	

		else:

			if "url" in request.values:
				url = request.values["url"]
				filename = secure_filename(url.split("/")[-1])

				if not allowed_file(filename):
					flash("Not allowed extension")
					return redirect(request.url)

				response = requests.get(url, stream=True)
				if response.status_code == 200:
					path = os.path.join(current_app.config.get("UPLOAD_FOLDER"), 
				                        filename)
					with open(path, "wb") as f:
						for chunk in response:
							f.write(chunk)

				else:
					flash("Unable to load file from given url.")
					return redirect(request.url)

			else:
				flash("No selected file")
				return redirect(request.url)	

		file_db = File(name=filename)
		db.session.add(file_db)

		return redirect(url_for("reports.parser"))

	return render_template("reports/loader.html")


@reports.route("/parser", methods=["GET"])
def parser():
	file_id = request.values.get("file_id")  
	if not file_id:
		abort(400) # BAD REQUEST

	try:
		file = db.session.query(File).filter_by(id=file_id).one()
	except NoResultFound:
		abort(404) # NOT FOUND

	filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], file.name)
	if not os.path.exists(filepath): 
		abort(500) # INTERNAL SERVER ERROR (no file)

	voc = create_vocabulary(db.session)
	spec = dict(
		bls=get_finrecords_reprs(db.session, "bls"),
		nls=get_finrecords_reprs(db.session, "nls"),
		cfs=get_finrecords_reprs(db.session, "cfs")
	)
	cspec = get_companies_reprs(db.session)
	report = FinancialReport(filepath, cspec=cspec, spec=spec, voc=voc, 
		                     last_page=10)

	# identify company in db
	try: 
		company = db.session.query(Company).\
		              filter_by(isin=report.company["isin"]).one()
	except (NoResultFound, AttributeError, KeyError):
		company = None

	return render_template("reports/parser.html", report=report, 
		                   company=company)