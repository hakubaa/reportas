import json

from flask import jsonify, request, g, abort, render_template
from flask.views import MethodView

from app.rapi.util import apply_query_parameters
from app.models import DBRequest, Permission
from app.user import auth
from app.user.auth import permission_required
from app import db


# class ContextMixin(object):
#     def get_context_data(self, **kwargs):
#         if "view" not in kwargs:
#             kwargs["view"] = self
#     return kwargs
    
    
# class SingleObjectMixin(ContextMixin):
#     model = None
#     context_object_name = None
#     id_url_kwarg = None
    
#     def get_context_object_name(self, obj = None):
#         if self.context_object_name:
#             return self.context_object_name
#         elif self.model:
#             return self.model.__name__.lower() + "_obj"
#         elif obj:
#             return obj.__class__.__name__.lower() + "_obj"
#         else:
#             return None
    
#     def get_object(self, **kwargs):
#         if not self.model:
#             raise RuntimeError("Model not defined")
#         obj = db.session.query(self.model).first()
#         return obj
        
#     def get_context_data(self, **kwargs):
#         object = self.get_object(object)
#         context_object_name = self.get_context_object_name(object)
#         context = dict()
#         if context_object_name:
#             context[context_object_name] = object
#         context.update(kwargs)
#         return super().get_context_data(**context)
        

# class FormMixin(ContextMixin):
#     form_class = None
#     success_url = None
    
#     def get_context_data(self, **kwargs):
#         if "form" not in kwargs:
#             kwargs["form"] = self.get_form()
#         return super().get_context_data(**kwargs)
    
#     def get_form_class(self):
#         return self.form_class
    
#     def get_form_kwargs(self):
#         return request.form
    
#     def get_success_url(self, **kwargs):
#         return self.success_url
        
#     def get_form(self, form_class=None):
#         if form_class is None:
#             from_class = self.get_form_class()
#         return form_class(**self.get_forms_kwargs())
        
#     def form_valid(self, form):
#         return redirect(self.success_url)
    
# class TemplateResponseMixin():
#     template_name = None
    
#     def get_template_name(self, **kwargs):
#         return self.template_name
        
        
    
    
# class ListView(MethodView):
#     model = None
#     context_object_name = None 
#     template = None
    
#     def get_context_object_name(self):
#         if self.context_object_name:
#             return self.context_object_name
#         elif self.model:
#             return self.model.__name__.lower() + "_list"
#         return None
        
#     def get_context_data(*args, **kwargs):
#         data = dict()
#         objs = db.session.query(self.model).all()
#         data[self.get_context_object_name()] = objs
#         return dict
    
#     def get_template(self, *args, **kwargs):
#         return self.template
        
#     def get_objects(self, *args, **kwargs):
#         objs = db.session.query(self.model).all()
#         return objs
    
#     def get(self, *args, **kwargs):
#         return render_template(
#             self.get_template(*args, **kwargs), 
#             **self.get_context_data(*args, **kwargs)
#         )


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
            
