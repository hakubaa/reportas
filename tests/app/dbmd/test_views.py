import base64
import json
import unittest
from datetime import datetime, date
import unittest.mock as mock
from urllib.parse import urlparse
import types

from marshmallow_sqlalchemy import ModelSchema
from marshmallow import fields
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from flask import url_for
from flask_login import current_user
from werkzeug.datastructures import MultiDict

from tests.app import AppTestCase, create_and_login_user

from app import db
from db.core import Model
from app.models import User, DBRequest, Role
import db.models as models
from db import records_factory
from app.dbmd import views

#-------------------------------------------------------------------------------
# CREATE TESTING ENVIRONMENT 
#-------------------------------------------------------------------------------

class Student(Model):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    age = Column(Integer)
    name = Column(String, nullable=False, unique=True)


class Account(Model):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    balance = Column(Integer, nullable=False)

    student_id = Column(Integer, ForeignKey("students.id"))
    student = relationship("Student", backref="accounts")


@records_factory.register_schema()
class AccountSchema(ModelSchema):
    class Meta:
        model = Account


@records_factory.register_schema()
class StudentSchema(ModelSchema):
    class Meta:
        model = Student
    
    accounts = fields.Nested(
        AccountSchema, only=("id", "balance"), many=True
    )


def create_user(name="Test", email="test@test.test", password="test"):
    Role.insert_roles()
    role = db.session.query(Role).filter_by(name="Administrator").one()
    user = User(name=name, email=email, password=password, role=role)
    db.session.add(user)
    db.session.commit()
    return user

def create_company(name="TEST", isin="#TEST"):
    company = models.Company(name=name, isin=isin)
    db.session.add(company)
    db.session.commit()
    return company

def create_ftype(name="ics"):
    ftype = models.FinancialStatementType(name=name)
    db.session.add(ftype)
    db.session.commit()
    return ftype

def create_rtype(name="TEST", ftype=None, timeframe="pot"):
    if not ftype:
        ftype = db.session.query(models.FinancialStatementType).one()
    rtype = models.RecordType(name=name, ftype=ftype, timeframe=timeframe)
    rtype.reprs.append(
        models.RecordTypeRepr(value="TEST REPR", lang="PL")
    )
    db.session.add(rtype)
    db.session.commit()
    return rtype

#-------------------------------------------------------------------------------

class IndexViewTest(AppTestCase):
    
    @create_and_login_user()
    def test_for_rendering_proper_template(self):
        response = self.client.get(url_for("admin.index"))
        self.assert_template_used("admin/index.html")
        
    def test_unauthenticated_users_are_redirected_to_login_page(self):
        response = self.client.get(url_for("admin.index"), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for("user.login"))

    
class ListCompaniesViewTest(AppTestCase):
    
    @create_and_login_user()
    def test_for_rendering_proper_template(self):
        response = self.client.get(url_for("company.index_view"))
        self.assert_template_used("admin/model/list.html") 
        
    @create_and_login_user()
    def test_for_displaying_companies_data(self):
        company1 = models.Company(isin="ISIN TEST", name="TEST")
        company2 = models.Company(isin="ISIN TEST #123", name="TEST2")
        db.session.add_all((company1, company2))
        db.session.commit()
        
        response = self.client.get(url_for("company.index_view"))
        
        self.assertInContent(response, company1.isin)
        self.assertInContent(response, company2.isin)

    def test_unauthenticated_users_are_redirected_to_login_page(self):
        response = self.client.get(url_for("company.index_view"), 
                                   follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse(response.location).path, url_for("user.login"))


class CreateCompanyViewTest(AppTestCase):
    
    @create_and_login_user()
    def test_for_rendering_proper_template(self):
        response = self.client.get(url_for("company.create_view"))
        self.assert_template_used("admin/model/create.html")    
        
    @create_and_login_user(pass_user=True)
    def test_post_request_with_all_data_creates_new_dbrequest(self, user):
        response = self.client.post(
            url_for("company.create_view"),
            data = dict(name="TEST", isin="#TEST", ticker="TICKER")
        )
        
        self.assertEqual(db.session.query(models.Company).count(), 0)
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "create")
        
        data = json.loads(dbrequest.data)
        self.assertEqual(data["isin"], "#TEST")
        self.assertEqual(data["ticker"], "TICKER")
        
    @create_and_login_user()
    def test_redirects_after_successful_post_request(self):
        response = self.client.post(
            url_for("company.create_view"),
            data = dict(name="TEST", isin="#TEST", ticker="TICKER")
        ) 
        self.assertRedirects(response, url_for("company.index_view"))
        
    @create_and_login_user()
    def test_form_populate_controls_after_unsuccessful_request(self):
        response = self.client.post(
            url_for("company.create_view"),
            data = dict(name="OPENSTOCK", ticker="TICKER#123")
        ) 
        form = self.get_context_variable("form")
        self.assertInContent(response, "TICKER#123")
        self.assertInContent(response, "OPENSTOCK")


class UpdateCompanyViewTest(AppTestCase):
    
    def create_company(self, isin="#TEST", name="TEST"):
        company = models.Company(isin=isin, name=name)
        db.session.add(company)
        db.session.commit()
        return company
        
    @create_and_login_user()
    def test_for_rendering_proper_template(self):
        company = self.create_company()
        response = self.client.get(url_for("company.edit_view", id=company.id))
        self.assert_template_used("admin/model/edit.html")
        
    @create_and_login_user()
    def test_redirects_to_list_view_when_company_does_not_exist(self):
        response = self.client.get(url_for("company.edit_view", id=1),
                                   follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for("company.index_view"), response.location)

    @create_and_login_user()  
    def test_form_is_populated_with_data_of_edited_object(self):
        company = self.create_company()
        response = self.client.get(url_for("company.edit_view", id=company.id))
        form = self.get_context_variable("form")
        self.assertEqual(form.name.data, company.name)
        self.assertEqual(form.isin.data, company.isin)
        
    @create_and_login_user(pass_user=True)
    def test_post_request_with_all_data_creates_new_dbrequest(self, user=True):
        company = self.create_company()
        response = self.client.post(
            url_for("company.edit_view", id=company.id),
            data = dict(name="NEW NAME", isin=company.isin)
        )
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "update")
        
        data = json.loads(dbrequest.data)
        self.assertEqual(data["name"], "NEW NAME")
        self.assertEqual(data["id"], company.id)
        
    @create_and_login_user()
    def test_redirects_after_successful_post_request(self):
        company = self.create_company()
        response = self.client.post(
            url_for("company.edit_view", id=company.id),
            data = dict(name="NEW NAME", isin=company.isin),
            follow_redirects=False
        )
        self.assertRedirects(response, url_for("company.index_view"))
        
    @create_and_login_user()
    def test_form_populate_controls_after_unsuccessful_request(self):
        company = self.create_company()
        response = self.client.post(
            url_for("company.edit_view", id=company.id),
            data = dict(name=None, ticker="TICKER#123")
        )
        form = self.get_context_variable("form")
        self.assertInContent(response, "TICKER#123")


class DeleteCompanyViewTest(AppTestCase):
    
    def create_company(self, isin="#TEST", name="TEST"):
        company = models.Company(isin=isin, name=name)
        db.session.add(company)
        db.session.commit()
        return company

    @create_and_login_user()
    def test_redirects_to_list_view_when_company_does_not_exist(self):
        response = self.client.post(url_for("company.delete_view", id=1),
                                   follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for("company.index_view"), response.location)

    @create_and_login_user(pass_user=True)
    def test_for_creating_dbrequest(self, user=True):
        company = self.create_company()
        response = self.client.post(
            url_for("company.delete_view", id=company.id)
        )
        
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "delete")
        
        data = json.loads(dbrequest.data)
        self.assertEqual(data["id"], company.id)
        
    @create_and_login_user()
    def test_redirects_after_request(self):
        company = self.create_company()
        response = self.client.post(
            url_for("company.delete_view", id=company.id),
            follow_redirects=False
        )
        self.assertRedirects(response, url_for("company.index_view"))


class CompanyViewFormTest(AppTestCase):

    def test_non_empty_fields(self):
        view = views.CompanyView(models.Company, db.session)
        form = view.get_form()()

        form.validate()

        self.assertIn("isin", form.errors)
        self.assertIn("name", form.errors)

    def test_view_s_form_validate_with_proper_data(self):
        view = views.CompanyView(models.Company, db.session)
        form = view.get_form()()

        form.process(formdata=MultiDict(dict(name="TEST", isin="#TEST")))
       
        self.assertTrue(form.validate())

    def test_sector_is_transformed_to_sector_id(self):
        sector = models.Sector(name="Media")
        db.session.add(sector)
        db.session.commit()

        view = views.CompanyView(models.Company, db.session)
        view.get_user = types.MethodType(lambda self: create_user(), view)
        form = view.get_form()()

        form.process(formdata=MultiDict(
            dict(name="TEST", isin="#TEST", sector=str(sector.id))
        ))
        validation_outcome = form.validate() 

        self.assertTrue(validation_outcome)

        dbrequest = view.create_model(form)
        data = json.loads(dbrequest.data)

        self.assertIn("sector_id", data)
        self.assertEqual(data["sector_id"], sector.id)


class CreateRecordTypeViewTest(AppTestCase):

    @create_and_login_user(pass_user=True)
    def test_post_request_with_all_data_creates_new_dbrequest(self, user):
        ftype = create_ftype()
        response = self.client.post(
            url_for("recordtype.create_view"),
            data = dict(name="TEST", ftype=ftype.id)
        )
        
        self.assertEqual(db.session.query(models.RecordType).count(), 0)
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "create")
        
        data = json.loads(dbrequest.data)
        self.assertEqual(data["name"], "TEST")
        self.assertEqual(data["ftype_id"], ftype.id)

    def test_name_and_statement_are_required(self):
        view = views.RecordTypeView(models.RecordType, db.session)
        form = view.get_create_form()()

        form.validate()

        errors = form.errors
        self.assertIn("name", errors)
        self.assertIn("ftype", errors)
        
    @create_and_login_user()
    def test_redirects_after_successful_post_request(self):
        ftype = create_ftype()
        response = self.client.post(
            url_for("recordtype.create_view"),
            data = dict(name="TEST", ftype=ftype.id)
        )
        self.assertRedirects(response, url_for("recordtype.index_view"))
        
    @create_and_login_user()
    def test_form_populate_controls_after_unsuccessful_request(self):
        response = self.client.post(
            url_for("recordtype.create_view"),
            data = dict(name="TEST NAME")
        )
        form = self.get_context_variable("form")
        self.assertInContent(response, "TEST NAME")

    def test_ftype_is_transformed_to_ftype_id(self):
        ftype = models.FinancialStatementType(name="bls")
        db.session.add(ftype)
        db.session.commit()

        view = views.RecordTypeView(models.RecordType, db.session)
        view.get_user = types.MethodType(lambda self: create_user(), view)
        form = view.get_form()()

        form.process(formdata=MultiDict(dict(
            ftype=str(ftype.id), name="TEST"
        )))
        validation_outcome = form.validate() 

        self.assertTrue(validation_outcome)

        dbrequest = view.create_model(form)
        data = json.loads(dbrequest.data)

        self.assertIn("ftype_id", data)
        self.assertEqual(data["ftype_id"], ftype.id)


class EditRecordTypeViewTest(AppTestCase):
        
    @create_and_login_user()
    def test_redirects_to_list_view_when_rtype_does_not_exist(self):
        response = self.client.get(
            url_for("recordtype.edit_view", id=1), follow_redirects=False
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for("recordtype.index_view"), response.location)

    @create_and_login_user()  
    def test_form_is_populated_with_data_of_edited_object(self):
        rtype = create_rtype(name="TEST", ftype=create_ftype())
        response = self.client.get(url_for("recordtype.edit_view", id=rtype.id))
        form = self.get_context_variable("form")
        self.assertEqual(form.name.data, rtype.name)
        self.assertEqual(form.ftype.data, rtype.ftype)
        
    @create_and_login_user(pass_user=True)
    def test_post_request_with_all_data_creates_new_dbrequest(self, user=True):
        ftype=create_ftype()
        rtype = create_rtype(name="TEST", ftype=ftype)
        response = self.client.post(
            url_for("recordtype.edit_view", id=rtype.id),
            data = dict(name="NEW NAME", id=rtype.id, ftype=ftype.id)
        )
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "update")
        
        data = json.loads(dbrequest.data)
        self.assertEqual(data["name"], "NEW NAME")
        self.assertEqual(data["id"], rtype.id)
        
    def test_name_and_statement_are_required(self):
        view = views.RecordTypeView(models.RecordType, db.session)
        form = view.get_edit_form()()

        form.validate()

        errors = form.errors
        self.assertIn("name", errors)
        self.assertIn("ftype", errors)


class DeleteRecordTypeViewTest(AppTestCase):


    @create_and_login_user()
    def test_redirects_to_list_view_when_company_does_not_exist(self):
        response = self.client.post(
            url_for("recordtype.delete_view", id=1), follow_redirects=False
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for("recordtype.index_view"), response.location)

    @create_and_login_user(pass_user=True)
    def test_for_creating_dbrequest(self, user=True):
        rtype = create_rtype(name="TEST", ftype=create_ftype())
        response = self.client.post(
            url_for("recordtype.delete_view", id=rtype.id)
        )
        
        self.assertEqual(db.session.query(DBRequest).count(), 1)
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "delete")
        
        data = json.loads(dbrequest.data)
        self.assertEqual(data["id"], rtype.id)
        
    @create_and_login_user()
    def test_redirects_after_request(self):
        rtype = create_rtype(name="TEST", ftype=create_ftype())
        response = self.client.post(
            url_for("recordtype.delete_view", id=rtype.id),
            follow_redirects=False
        )
        self.assertRedirects(response, url_for("recordtype.index_view"))


class ReportViewFormTest(AppTestCase):

    def test_non_empty_fields(self):
        view = views.ReportView(models.Report, db.session)
        form = view.get_form()()

        form.validate()

        self.assertIn("timestamp", form.errors)
        self.assertIn("timerange", form.errors)
        self.assertIn("company", form.errors)

    def test_view_s_form_validate_with_proper_data(self):
        company = models.Company(name="TEST", isin="TEST")
        db.session.add(company)
        db.session.commit()

        view = views.ReportView(models.Report, db.session)
        form = view.get_form()()

        form.process(formdata=MultiDict(dict(
            company=str(company.id), timestamp="2015-03-31", timerange=12
        )))
       
        self.assertTrue(form.validate())

    def test_company_is_transformed_to_company_id(self):
        company = models.Company(name="TEST", isin="TEST")
        db.session.add(company)
        db.session.commit()

        view = views.ReportView(models.Report, db.session)
        view.get_user = types.MethodType(lambda self: create_user(), view)
        form = view.get_form()()

        form.process(formdata=MultiDict(dict(
            company=str(company.id), timestamp="2015-03-31", timerange=12
        )))
        validation_outcome = form.validate() 

        self.assertTrue(validation_outcome)

        dbrequest = view.create_model(form)
        data = json.loads(dbrequest.data)

        self.assertIn("company_id", data)
        self.assertEqual(data["company_id"], company.id)


class RecordViewFormTest(AppTestCase):

    def test_non_empty_fields(self):
        view = views.RecordView(models.Record, db.session)
        form = view.get_form()()

        form.validate()

        self.assertIn("timestamp", form.errors)
        self.assertIn("timerange", form.errors)
        self.assertIn("company", form.errors)
        self.assertIn("value", form.errors)
        self.assertIn("rtype", form.errors)

    def test_view_s_form_validate_with_proper_data(self):
        company = create_company()
        rtype = create_rtype(name="A", ftype=create_ftype())

        view = views.RecordView(models.Record, db.session)
        form = view.get_form()()

        form.process(formdata=MultiDict(dict(
            company=str(company.id), timestamp="2015-03-31", timerange=12,
            rtype=str(rtype.id), value=100
        )))
       
        self.assertTrue(form.validate())

    def test_company_and_rtype_are_transformed_to_ids(self):
        company = create_company()
        rtype = create_rtype(name="A", ftype=create_ftype())

        view = views.RecordView(models.Record, db.session)
        view.get_user = types.MethodType(lambda self: create_user(), view)
        form = view.get_form()()

        form.process(formdata=MultiDict(dict(
            company=str(company.id), timestamp="2015-03-31", timerange=12,
            rtype=str(rtype.id), value=100
        )))
        validation_outcome = form.validate() 

        self.assertTrue(validation_outcome)

        dbrequest = view.create_model(form)
        data = json.loads(dbrequest.data)

        self.assertIn("company_id", data)
        self.assertEqual(data["company_id"], company.id)

        self.assertIn("rtype_id", data)
        self.assertEqual(data["rtype_id"], rtype.id)


class DBRequestViewTest(AppTestCase):

    def create_dbrequest(
        self, action="create", data={"name": "Python", "age": 17}
    ):
        request = DBRequest(
            model="Student", action=action, user=None, data=json.dumps(data)   
        )
        db.session.add(request)
        db.session.commit()
        return request


    @create_and_login_user
    def test_index_view_renders_proper_template(self):
        response = self.client.get(url_for("dbrequest.index_view"))
        self.assert_template_used("admin/model/dbrequest_list.html")

    @create_and_login_user(role_name="User")
    def test_user_without_proper_permissions_can_t_accept_requests(self):
        response = self.client.post(
            url_for("dbrequest.action_view"), 
            data=dict(action="accept", rowid="1"),
            follow_redirects=False
        )
        self.assertEqual(response.status_code, 403)

    @create_and_login_user(role_name="Moderator")
    @mock.patch.object(DBRequest, "execute")
    def test_dbrequests_are_executed_when_being_accepted(self, class_method):
        request = self.create_dbrequest()
        response = self.client.post(
            url_for("dbrequest.action_view"), 
            data=dict(action="accept", rowid=request.id),
            follow_redirects=False
        )
        self.assertTrue(class_method.called)

    @unittest.skip
    @create_and_login_user(role_name="Moderator", pass_user=True)
    @mock.patch.object(DBRequest, "execute")
    def test_current_user_is_set_as_moderator(self, class_method, user):
        request = self.create_dbrequest()
        response = self.client.post(
            url_for("dbrequest.action_view"), 
            data=dict(action="accept", rowid=request.id),
            follow_redirects=False
        )
        self.assertEqual(class_method.call_args[0][0], user)

    @create_and_login_user(role_name="Moderator")
    def test_accepting_create_request_creates_new_object(self):
        request = self.create_dbrequest()

        response = self.client.post(
            url_for("dbrequest.action_view"), 
            data=dict(action="accept", rowid=request.id)
        )

        self.assertEqual(db.session.query(Student).count(), 1)

        student = db.session.query(Student).one()
        self.assertEqual(student.name, "Python")

    @create_and_login_user(role_name="Moderator")
    def test_accepting_delete_request_removes_the_object(self):
        student = Student(name="Python", age=17)
        db.session.add(student)
        db.session.commit()
        request = self.create_dbrequest(
            action="delete", data=dict(id=student.id)
        )

        response = self.client.post(
            url_for("dbrequest.action_view"), 
            data=dict(action="accept", rowid=request.id)
        )

        self.assertEqual(db.session.query(Student).count(), 0)

    @create_and_login_user(role_name="Moderator")
    def test_database_errors_are_saved_in_dbrequest(self):
        student = Student(name="Python", age=17)
        db.session.add(student)
        db.session.commit()

        request = self.create_dbrequest()

        response = self.client.post(
            url_for("dbrequest.action_view"), 
            data=dict(action="accept", rowid=request.id)
        )

        self.assertIsNotNone(request.errors)
        self.assertIn("database", request.errors)

    @create_and_login_user(role_name="Moderator", pass_user=True)
    def test_accept_subrequest_before_main_request(self, user):
        main_request = DBRequest(
            model="Student", user=user, action="create", 
            data=json.dumps({"name": "Python", "age": 17})
        )
        subrequest = DBRequest(
            model="Account", user=user, action="create",
            data=json.dumps({"balance": 1500})
        )
        main_request.add_subrequest(subrequest)
        db.session.add(main_request)
        db.session.add(subrequest)
        db.session.commit()

        response = self.client.post(
            url_for("dbrequest.action_view"), 
            data=dict(action="accept", rowid=subrequest.id)
        )

        self.assertTrue(subrequest.executed)
        self.assertFalse(main_request.executed)

    @create_and_login_user(role_name="Moderator", pass_user=True)
    @mock.patch("db.models.Record.create_synthetic_records")
    def test_accept_calls_create_synthetic_records(self, csr_mock, user):
        csr_mock.return_value = list()
        company = create_company()
        rtype = create_rtype(ftype=create_ftype(name="ics"))

        request = DBRequest(
            model="Record", user=user, action="create", 
            data=json.dumps({
                "company_id": company.id, "rtype_id": rtype.id,
                "value": 900, "timerange": 6, "timestamp": "2016-12-31"
            })
        )
        db.session.add(request)
        db.session.commit()

        response = self.client.post(
            url_for("dbrequest.action_view"), 
            data=dict(action="accept", rowid=request.id)
        )

        self.assertTrue(csr_mock.called)
        
        record = db.session.query(models.Record).one()
        self.assertEqual(csr_mock.call_args[0], (db.session, [record]))


    @create_and_login_user(role_name="Moderator", pass_user=True)
    @mock.patch("db.models.Record.create_synthetic_records")
    def test_accept_does_not_call_crs_for_non_records(self, csr_mock, user):
        request = DBRequest(
            model="Student", user=user, action="create", 
            data=json.dumps({"name": "Python", "age": 17})
        )
        db.session.add(request)
        db.session.commit()

        response = self.client.post(
            url_for("dbrequest.action_view"), 
            data=dict(action="accept", rowid=request.id)
        )

        self.assertFalse(csr_mock.called)


class RecordFormulaViewFormTest(AppTestCase):

    def test_non_empty_fields(self):
        view = views.RecordFormulaView(models.RecordFormula, db.session)
        form = view.get_form()()

        form.validate()

        self.assertIn("rtype", form.errors)

    def test_form_validate_with_proper_data(self):
        rtype = create_rtype(name="A", ftype=create_ftype())

        view = views.RecordFormulaView(models.RecordFormula, db.session)
        form = view.get_form()()

        form.process(formdata=MultiDict(dict(rtype=str(rtype.id))))
       
        self.assertTrue(form.validate())

    def test_rtype_is_transformed_to_rtype_id(self):
        rtype = create_rtype(name="A", ftype=create_ftype())

        view = views.RecordFormulaView(models.RecordFormula, db.session)
        view.get_user = types.MethodType(lambda self: create_user(), view)
        form = view.get_form()()

        form.process(formdata=MultiDict(dict(rtype=str(rtype.id))))
        validation_outcome = form.validate() 

        self.assertTrue(validation_outcome)

        dbrequest = view.create_model(form)
        data = json.loads(dbrequest.data)

        self.assertIn("rtype_id", data)
        self.assertEqual(data["rtype_id"], rtype.id)