import json

from flask import jsonify, request, g, abort
from flask.views import MethodView

from app.rapi.util import apply_query_parameters
from app.models import DBRequest, Permission
from app.user import auth
from app.user.auth import permission_required
from app import db


class ViewUtilMixin(object):

    def get_schema(self):
        fields = request.values.get("fields", None)
        if fields: fields = "".join(fields.split()).split(",")
        schema = self.schema(only=fields)
        return schema

    def modify_data(self, data):
        return data

    def create_dbrequest(self, action, user, **kwargs):
        data = dict()
        request_data = request.data.decode()
        if request_data:
            data.update(json.loads(request_data))
        data.update(kwargs)
        data = self.modify_data(data)
        dbrequest = DBRequest(
            data=json.dumps(data), user=user, action=action, 
            model=self.model.__name__
        )
        return dbrequest


class DetailView(ViewUtilMixin, MethodView):
    model = None
    schema = None

    def get_object(self, id):
        obj = db.session.query(self.model).get(id)
        if not obj:
            abort(404)
        return obj

    @auth.login_required
    @permission_required(Permission.READ_DATA)
    def get(self, *args, **kwargs):
        obj = self.get_object(*args, **kwargs)
        schema = self.get_schema()
        data = schema.dump(obj).data
        return jsonify(data), 200

    @auth.login_required
    @permission_required(Permission.MODIFY_DATA)
    def delete(self, *args, **kwargs):
        obj = self.get_object(*args, **kwargs)
        dbrequest = self.create_dbrequest("delete", g.user, **kwargs)
        db.session.add(dbrequest)
        db.session.commit()
        return jsonify({}), 202

    @auth.login_required
    @permission_required(Permission.MODIFY_DATA)
    def put(self, *args, **kwargs):
        obj = self.get_object(*args, **kwargs)
        dbrequest = self.create_dbrequest("update", g.user, **kwargs)
        db.session.add(dbrequest)
        db.session.commit()
        return jsonify({}), 202   


class ListView(ViewUtilMixin, MethodView):
    model = None
    schema = None

    def get_objects(self, *args, **kwargs):
        objs = db.session.query(self.model)
        return objs

    @auth.login_required
    @permission_required(Permission.READ_DATA)
    def get(self, *args, **kwargs):
        objs = apply_query_parameters(self.get_objects(*args, **kwargs))
        schema = self.get_schema()
        data = schema.dump(objs, many=True).data
        return jsonify({
            "results": data,
            "count": len(data)
        }), 200

    @auth.login_required
    @permission_required(Permission.MODIFY_DATA)
    def post(self, *args, **kwargs):
        dbrequest = self.create_dbrequest("create", g.user, **kwargs)
        db.session.add(dbrequest)
        db.session.commit()
        return jsonify({}), 202