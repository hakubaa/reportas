import json

from flask import jsonify, request, g, abort, render_template, redirect
from flask_login import login_required
from flask.views import MethodView

from app.rapi.util import apply_query_parameters
from app.models import DBRequest, Permission
from app.user import auth
from app.user.auth import permission_required
from app import db


class ContextMixin(object):
    def get_context_data(self, **kwargs):
        if "view" not in kwargs:
            kwargs["view"] = self
        return kwargs


class MultipleObjectMixin(ContextMixin):
    model = None
    context_object_name = None

    def get_objects(self):
        return db.session.query(self.model).all()

    def get_context_object_name(self):
        if self.context_object_name:
            return self.context_object_name
        elif self.model:
            return self.model.__name__.lower() + "_list"
        else:
            return None

    def get_context_data(self, **kwargs):
        context_object_name = self.get_context_object_name()
        context = dict()
        if context_object_name:
            context[context_object_name] = self.get_objects()
        context.update(kwargs)
        return super().get_context_data(**context)


class SingleObjectMixin(ContextMixin):
    model = None
    context_object_name = None
    id_url_kwarg = None
    
    def get_context_object_name(self):
        if self.context_object_name:
            return self.context_object_name
        elif self.model:
            return self.model.__name__.lower() + "_obj"
        else:
            return None
    
    def get_object(self, **kwargs):
        if not self.model:
            raise RuntimeError("Model not defined")
        obj_id = kwargs.get(self.id_url_kwarg or "id")
        if not obj_id:
            raise RuntimeError("No <id> to identify the object")
        obj = db.session.query(self.model).get(obj_id)
        if not obj:
            abort(404)
        return obj
        
    def get_context_data(self, **kwargs):
        context_object_name = self.get_context_object_name()
        context = dict()
        if context_object_name:
            context[context_object_name] = self.get_object(**kwargs)
        context.update(kwargs)
        return super().get_context_data(**context)


class FormMixin(ContextMixin):
    form_class = None
    success_url = None
    
    def get_context_data(self, **kwargs):
        if "form" not in kwargs:
            kwargs["form"] = self.get_form(**kwargs)
        return super().get_context_data(**kwargs)
    
    def get_form_class(self):
        return self.form_class
    
    def get_form_kwargs(self):
        return request.form
    
    def get_success_url(self, **kwargs):
        return self.success_url
        
    def get_form(self, **kwargs):
        form_class = self.get_form_class()
        instance=None
        if hasattr(self, "get_object"):
            instance = self.get_object(**kwargs)
        return form_class(**self.get_form_kwargs(), obj=instance)
        
    def form_valid(self, form, **kwargs):
        return redirect(self.get_success_url())

    def form_invalid(self, form, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))


class TemplateResponseMixin(object):
    template_name = None

    def get_template_name(self):
        return self.template_name

    def render_to_response(self, context):
        return render_template(self.get_template_name(), **context) 


class ProcessFormView(FormMixin, TemplateResponseMixin, MethodView):

    @login_required
    def get(self, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))

    @login_required
    def post(self, **kwargs):
        form = self.get_form(**kwargs)
        if form.validate():
            return self.form_valid(form, **kwargs)
        else:
            return self.form_invalid(form, **kwargs)


class ListView(TemplateResponseMixin, MultipleObjectMixin, MethodView):

    @login_required
    def get(self, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))

  
class DetailView(TemplateResponseMixin, SingleObjectMixin, MethodView):

    @login_required
    def get(self, **kwargs):
        return self.render_to_response(self.get_context_data(**kwargs))


class CreateView(ProcessFormView):
    pass


class UpdateView(SingleObjectMixin, ProcessFormView):
    pass



# class FormView(MethodView):
#     model = None
#     form = None
#     template = None
#     context_object_name = None
    
#     def get_context_object_name(self):
#         if self.context_object_name:
#             return self.context_object_name
#         elif self.model:
#             return self.modal.__name__.lower() + "_obj"
#         return None
    
#     def get_object(self, id=None):
#         if not id:
#             return None
#         return db.session.query(self.model).first()
        
#     def get_context_data(*args, **kwargs):
#         context_object_name = self.get_context_object_name()
#         object = self.get_object(*args, **kwargs)
        
#         data = dict()
#         if context_object_name:
#             data[context_object_name] = object
#         data["form"] = self.form(request.form, obj=object)
        
#         return data
        
#     def get(self, *args, **kwargs):
#         return render_template(
#             self.get_template(*args, **kwargs),
#             **self.get_context_data(*args, **kwargs)
#         )

#     def post(self, *args, **kwargs):
#         context = self.get_context_data()
#         if context["form"].validate_on_submit():
#             action = "create"
#             if context[self.get_context_object_name()]:
#                 action = "update"
                
#             dbrequest = DBRequest(
#                 action=action, user = current_user,
#                 model = "Company", data = json.dumps(request.form)
#             )
#             try:
#                 db.session.add(dbrequest)
#                 db.session.commit()
#                 flash("OK")
#             except Exception: # change to base sqlalchemy exception
#                 db.session.rollback()
#                 flash("FUCK")
#             else:
#                 return redirect(url_for("dbmd.list_companies"))
#         else:
#             return render_template(
#                 self.get_template(*args, **kwargs),
#                 **self.get_context_data(*args, **kwargs)
#             )
            
