import json

from flask import abort, flash, redirect, render_template, url_for, request
from flask_login import current_user, login_required

from app import db
from app.dbmd.forms import CompanyForm
from app.dbmd import dbmd
from app.user import auth
from app.models import DBRequest
from db.models import Company
from app.dbmd.base import ListView, DetailView, CreateView, UpdateView



@dbmd.route("/", methods=["GET"])
@login_required
def index():
    return render_template("dbmd/index.html")
    


#-------------------------------------------------------------------------------
# /companies/
#-------------------------------------------------------------------------------

class CompanyListView(ListView):
    template_name = "dbmd/companies/companies.html"
    model = Company
    context_object_name = "companies"


dbmd.add_url_rule(
    "/companies", view_func=CompanyListView.as_view("list_companies")
)

# @dbmd.route("/company/<int:id>", methods=["GET"])
# @login_required
# def company_detail(id):
#     company = db.session.query(Company).get(id)
#     if not company:
#         abort(404)
#     return render_template(
#         "dbmd/companies/company_detail.html", company=company
#     )


class CompanyDetailView(DetailView):
    template_name = "dbmd/companies/company_detail.html"
    model = Company
    context_object_name = "company"

dbmd.add_url_rule(
    "/companies/<int:id>", view_func=CompanyDetailView.as_view("company_detail")
)

# @dbmd.route("/companies", methods=["GET"])
# @login_required
# def list_companies():
#     companies = db.session.query(Company).all()
#     return render_template(
#         "dbmd/companies/companies.html",
#          companies=companies, title="Departments"
#     )


class CompanyCreateView(CreateView):
    model = Company
    template_name = "dbmd/companies/company.html"
    form_class = CompanyForm

    def get_success_url(self, **kwargs):
        return url_for("dbmd.list_companies")

    def form_valid(self, form):
        dbrequest = DBRequest(
            action="create", user = current_user,
            model = "Company", data = json.dumps(self.get_form_kwargs())
        )
        db.session.add(dbrequest)
        db.session.commit()

        flash("Your request has been registered.")
        return super().form_valid(form)


dbmd.add_url_rule(
    "/companies/add", view_func=CompanyCreateView.as_view("add_company")
)


# @dbmd.route('/companies/add', methods=["GET", "POST"])
# @login_required
# def add_company():
#     '''Create new company.'''
#     form = CompanyForm(formdata=request.form)
#     if form.validate_on_submit():
#         dbrequest = DBRequest(
#             action="create", user = current_user,
#             model = "Company", data = json.dumps(request.form)
#         )
#         try:
#             db.session.add(dbrequest)
#             db.session.commit()
#             flash("OK")
#         except Exception: # change to base sqlalchemy exception
#             db.session.rollback()
#             flash("FUCK")
#         else:
#             return redirect(url_for("dbmd.list_companies"))
#     return render_template(
#         "dbmd/companies/company.html", form=form, action="Add", 
#         add_company=True
#     )


class CompanyUpdateView(UpdateView):
    model = Company
    template_name = "dbmd/companies/company.html"
    form_class = CompanyForm

    def get_success_url(self, **kwargs):
        return url_for("dbmd.list_companies")

    def form_valid(self, form):
        dbrequest = DBRequest(
            action="update", user = current_user,
            model = "Company", data = json.dumps(self.get_form_kwargs())
        )
        db.session.add(dbrequest)
        db.session.commit()

        flash("Your request has been registered.")
        return super().form_valid(form)


dbmd.add_url_rule(
    "/companies/<int:id>/edit", view_func=CompanyUpdateView.as_view("edit_company")
)


# @dbmd.route('/companies/<int:id>/edit', methods=["GET", "POST"])
# @login_required
# def edit_company(id):
#     """Edit a company."""
#     company = db.session.query(Company).first()
#     if not company:
#         abort(404)
        
#     form = CompanyForm(request.form, obj=company, edit_mode=True)
#     if form.validate_on_submit():
#         data = request.form.to_dict()
#         data["id"] = id
#         dbrequest = DBRequest(
#             action="update", user = current_user,
#             model = "Company", data = json.dumps(data)
#         )
#         try:
#             db.session.add(dbrequest)
#             db.session.commit()
#             flash("OK")
#         except Exception: # change to base sqlalchemy exception
#             db.session.rollback()
#             flash("FUCK")
#         else:
#             return redirect(url_for("dbmd.list_companies"))  
        
#     return render_template(
#         "dbmd/companies/company.html", form=form, action="Edit",
#         add_company=False
#     )


@dbmd.route('/companies/<int:id>/delete', methods=["GET", "POST"])
@login_required
def delete_company(id):
    """Delete a company from the database."""
    
    company = db.session.query(Company).first()
    if not company:
        abort(404)
        
    dbrequest = DBRequest(
        action="delete", user = current_user,
        model = "Company", data = json.dumps({"id": company.id})
    )
    try:
        db.session.add(dbrequest)
        db.session.commit()
    except Exception: # change to base sqlalchemy exception
        db.session.rollback()
        flash("FUCK")
    else:
        flash('You have successfully deleted the company.')
    
    return redirect(url_for("dbmd.list_companies"))  

#-------------------------------------------------------------------------------
# /rtypes/
#-------------------------------------------------------------------------------

# class RecordTypeListView(ListView):
#     model = RecordType
#     context_object_name = "rtypes"
#     template = "dbmd/rtypes/rtypes.html"
    
#-------------------------------------------------------------------------------
# /records/
#-------------------------------------------------------------------------------   
    
# class RecordTypeListView(ListView):
#     model = Record
#     context_object_name = "records"
#     template = "dbmd/records/records.html"   
    


