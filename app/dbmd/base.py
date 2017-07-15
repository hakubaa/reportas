import json

from flask import url_for, redirect, request, flash, abort
from flask_login import current_user
from flask_admin.contrib import sqla
from flask_admin.babel import gettext

from app.models import DBRequest
from app.rapi.util import DatetimeEncoder


class PermissionRequiredMixin(object):
    default_permissions = 0x00
    create_view_permissions = None
    edit_view_permissions = None
    delete_view_permissions = None
    index_view_permissions = None
    details_view_permissions = None
    action_view_permissions = None

    def _handle_view(self, name, **kwargs):
        if not current_user.is_authenticated:
            return self.unauthorized_access()

        permissions = self.get_permissions(name)
        if not current_user.can(permissions):
            return self.forbidden_access()

        return None #access granted

    def unauthorized_access(self):
        return redirect(url_for("user.login", next=request.url))

    def forbidden_access(self):
        return abort(403)

    def get_permissions(self, name):
        if name.startswith("index"):
            return self.index_view_permissions or self.default_permissions

        if name.startswith("create"):
            return self.create_view_permissions or self.default_permissions

        if name.startswith("edit") or name.startswith("update"):
            return self.edit_view_permissions or self.default_permissions

        if name.startswith("delete"):
            return self.delete_view_permissions or self.default_permissions

        if name.startswith("detail"):
            return self.details_view_permissions or self.default_permissions

        if name.startswith("action"):
            return self.action_view_permissions or self.default_permissions

        return self.default_permissions

    @property
    def can_create(self):
        return self.check_permission("create")

    @property
    def can_edit(self):
        return self.check_permission("edit") 

    @property
    def can_delete(self):
        return self.check_permission("delete") 

    @property
    def can_action(self):
        return self.check_permission("action")

    def check_permission(self, action):
        if not current_user or not current_user.is_authenticated:
            return False

        permissions = self.get_permissions(action)
        if not current_user.can(permissions):
            return False

        return True


class DBRequestMixin(object):
    model_name = None

    def get_user(self):
        return current_user

    def get_model_name(self):
        if self.model_name:
            return self.model_name
        elif hasattr(self, "model") and self.model:
            return self.model.__name__
        else:
            return None

    def modify_data(self, data):
        return data

    def _create_dbrequest(self, action, data):
        dbrequest = DBRequest(
            action=action, user=self.get_user(),
            model=self.get_model_name(), 
            data = json.dumps(self.modify_data(data), cls=DatetimeEncoder)
        )
        self.session.add(dbrequest)
        try:
            self.session.commit()
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext("Failed to create request. %(error)s", 
                              error=str(ex)), "error")
                sqla.log.exception("Failed to create request.")
            return False
        else:
            flash("The request has been registered.") 
        return dbrequest

    def create_model(self, form):
        return self._create_dbrequest("create", form.data)

    def update_model(self, form, model):
        data = form.data
        data["id"] = model.id
        return self._create_dbrequest("update", data)

    def delete_model(self, model):
        data = dict(id=model.id)
        return self._create_dbrequest("delete", data)