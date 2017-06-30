import json

from flask import (
    current_app, make_response, render_template, jsonify, request, g
)
from flask_login import current_user

from app import debugtoolbar, db
from app.models import DBRequest, Permission
from app.rapi import api, rapi
from app.rapi import resources as res
from app.user import auth
from app.user.auth import permission_required
import db.models as models
from app.rapi import schemas


@rapi.route("/companies", methods=["GET", "POST"])
@auth.login_required
@permission_required(Permission.MODIFY_DATA)
def company_list():
    if request.method == "GET":

        objs = db.session.query(models.Company).all()
        schema = schemas.CompanySimpleSchema()
        data = schema.dump(objs, many=True).data
        return jsonify({
            "results": data,
            "count": len(data)
        }), 200

    elif request.method == "POST":

        dbrequest = DBRequest(data=request.data.decode(), user=g.user, 
                              action="create", model="Company")
        db.session.add(dbrequest)
        db.session.commit()

        return jsonify({}), 201



@rapi.route("/companies/<int:id>", methods=["GET"])
def company():
    return jsonify({}), 200


# api.add_resource(res.Root, "/", endpoint="root")
# api.add_resource(res.CompanyList, "/companies", endpoint="company_list")
# api.add_resource(res.CompanyDetail, "/companies/<int:id>", endpoint="company")
# api.add_resource(res.CompanyReprList, "/companies/<int:id>/reprs", 
#                  endpoint="crepr_list")
# api.add_resource(res.CompanyRecordList, "/companies/<int:id>/records",
#                  endpoint="company_record_list")
# api.add_resource(res.CompanyRecordDetail, "/companies/<int:id>/records/<int:rid>",
#                  endpoint="company_record")
# api.add_resource(res.CompanyReportList, "/companies/<int:id>/reports",
#                  endpoint="company_report_list")

# api.add_resource(res.RecordTypeList, "/rtypes", endpoint="rtype_list")
# api.add_resource(res.RecordTypeDetail, "/rtypes/<int:id>", endpoint="rtype")
# api.add_resource(res.RecordTypeReprList, "/rtypes/<int:id>/reprs",
#                  endpoint="rtype_repr_list")
# api.add_resource(res.RecordTypeReprDetail, "/rtypes/<int:id>/reprs/<int:rid>",
#                  endpoint="rtype_repr")

# api.add_resource(res.RecordList, "/records", endpoint="record_list")
# api.add_resource(res.RecordDetail, "/records/<int:id>", endpoint="record")

# api.add_resource(res.ReportList, "/reports", endpoint="report_list")
# api.add_resource(res.ReportDetail, "/reports/<int:id>", endpoint="report")
# api.add_resource(res.ReportList, "/reports/<int:id>/records", 
#                  endpoint="report_record_list")
# api.add_resource(res.ReportList, "/reports/<int:id>/records/<int:rid>", 
#                  endpoint="report_record")


# @rapi.after_request
# def after_request(response):
#     # Wrap JSON responses by HTML and ask flask-debugtoolbar to inject 
#     # own HTML into it
#     if (current_app.config.get("DEBUG_TB_ENABLED", False) 
#             and response.mimetype == "application/json" 
#             and response.status_code != 401
#     ):
#         # response.direct_passthrough = False
#         args = dict(response=response.data.decode("utf-8"), 
#                     http_code=response.status)
#         html_wrapped_response = make_response(
#             render_template("wrap_json.html", **args), response.status_code
#         )
#         # response = debugtoolbar.process_response(html_wrapped_response)
#         response = html_wrapped_response

#     return response


