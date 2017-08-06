import unittest

from sqlalchemy import Column, Integer, String
from flask_admin.contrib import sqla
from flask import url_for

from app.models import User, Role, Permission
from app import db
from db.core import Model
from app.dbmd import dbmd
from app.dbmd.base import PermissionRequiredMixin

from tests.app import AppTestCase, create_and_login_user

#-------------------------------------------------------------------------------
# CREATE TESTING ENVIRONMENT 
#-------------------------------------------------------------------------------

class Student(Model):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True)
    age = Column(Integer)
    name = Column(String, nullable=False)


class StudentView(PermissionRequiredMixin, sqla.ModelView):
    index_view_permissions = Permission.BROWSE_DATA
    create_view_permissions = Permission.CREATE_REQUESTS
    edit_view_permissions = Permission.CREATE_REQUESTS
    delete_view_permissions = Permission.CREATE_REQUESTS


dbmd.add_view(StudentView(Student, db.session))

#-------------------------------------------------------------------------------

class PermissionRequiredMixinTest(AppTestCase):
    models = [Student, User, Role]

    @create_and_login_user(role_name="Administrator")
    def test_testing_environment(self):
        response = self.client.get(url_for("student.index_view"))
        self.assertEqual(response.status_code, 200)
        self.assertInContent(response, "There are no items in the table.")

    def test_anonymouse_users_are_redirected_to_login_page_from_index_view(self):
        response = self.client.get(
            url_for("student.index_view"), follow_redirects=False
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for("user.login"), response.location)

    def test_anonymouse_users_are_redirected_to_login_page_from_create_view(self):
        response = self.client.get(
            url_for("student.create_view"), follow_redirects=False
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for("user.login"), response.location)

    def test_anonymouse_users_are_redirected_to_login_page_from_edit_view(self):
        response = self.client.get(
            url_for("student.edit_view"), follow_redirects=False
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for("user.login"), response.location)

    def test_anonymouse_users_are_redirected_to_login_page_from_delete_view(self):
        response = self.client.post(
            url_for("student.delete_view"), follow_redirects=False
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(url_for("user.login"), response.location)

    @create_and_login_user(role_name="Visitor")
    def test_users_without_permission_to_create_requests_get_403_code(self):
        response = self.client.get(
            url_for("student.create_view"), follow_redirects=False
        )
        self.assertEqual(response.status_code, 403)

    @create_and_login_user(role_name="Visitor")
    def test_rende_proper_template_when_403(self):
        response = self.client.get(url_for("student.create_view"))
        self.assert_template_used("403.html")  

    @create_and_login_user(role_name="Visitor")
    def test_users_without_permission_to_edit_requests_get_403_code(self):
        response = self.client.get(
            url_for("student.edit_view"), follow_redirects=False
        )
        self.assertEqual(response.status_code, 403)

    @create_and_login_user(role_name="Visitor")
    def test_users_without_permission_to_delete_requests_get_403_code(self):
        response = self.client.post(
            url_for("student.delete_view"), follow_redirects=False
        )
        self.assertEqual(response.status_code, 403)