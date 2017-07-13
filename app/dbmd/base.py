import json

from flask import url_for, redirect, request, flash
from flask_admin import base as admin_base
from flask_login import current_user
from flask_admin.contrib import sqla
from flask_admin.babel import gettext

from app.models import DBRequest
from app.rapi.util import DatetimeEncoder


class FlaskLoginMixin(object):

    def is_accessible(self):
        return current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for("user.login", next=request.url))


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
        

class AdminIndexView(FlaskLoginMixin, admin_base.AdminIndexView):
    pass
    

class ModelView(FlaskLoginMixin, sqla.ModelView):
    pass