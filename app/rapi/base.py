import json
import operator

from flask import jsonify, request, g, abort
from flask.views import MethodView
from sqlalchemy.orm.query import Query

from app.rapi.utils import *
from app.models import DBRequest, Permission
from app.user import auth
from app.user.auth import permission_required
from app import db


def create_http_request_handler(action, permissions=Permission.CREATE_REQUESTS):
    '''Factory of methods to handle http requests (used in ListView).'''
    def http_method(self, *args, **kwargs):
        dbrequests = self.create_dbrequests(action, g.user, **kwargs)
        db.session.add_all(dbrequests)
        db.session.commit()
        return jsonify({}), 202
    return auth.login_required(permission_required(permissions)(http_method))


class QueryStringParserMixin(object):
    parser = None

    def get_query_params(self, field=None):
        params = self.parser.get_params()
        if field is not None:
            return params.get(field, None)
        else:
            return params


class QueryParametersMixin(object):

    filter_operators = [
        QueryFilter(
            operator="=", method_query=operator.eq, 
            method_list=apply_conversion(operator.eq)
        ),
        QueryFilter(
            operator="<=", method_query=operator.le,
            method_list=apply_conversion(operator.le)
        ),
        QueryFilter(
            operator="<", method_query=operator.lt,
            method_list=apply_conversion(operator.lt)
        ),
        QueryFilter(
            operator="!=", method_query=operator.ne,
            method_list=apply_conversion(operator.ne)
        ),
        QueryFilter(
            operator=">=", method_query=operator.ge,
            method_list=apply_conversion(operator.ge)
        ),
        QueryFilter(
            operator=">", method_query=operator.gt,
            method_list=apply_conversion(operator.gt)
        ),
        QueryFilter(
            operator="@in@", method_query=lambda c, v: c.in_(v.split(",")),
            method_list=qlist_in_operator
        )
    ]
    filter_columns = []
    filter_overrides = {}

    enable_filter = True
    enable_sort = True
    enable_slice = True

    def apply_query_parameters(self, obj, params):
        if isinstance(obj, Query):
            modifiers = self.create_modifiers_for_query() 
        else:
            modifiers = self.create_modifiers_for_list()

        obj = modifiers["filter"](obj, params.get("filter", []))
        obj = modifiers["sort"](obj, params.get("sort", []))
        obj = modifiers["slice"](
            obj, params.get("limit", None), params.get("offset", None)
        )

        return obj

    def create_modifiers_for_query(self):
        modifiers = self.create_empty_qmethods()
        if self.enable_filter:
            modifiers["filter"] = FilterQueryModifier(
                operators=self.filter_operators,
                columns=self.filter_columns,
                overrides=self.filter_overrides
            )
        if self.enable_sort:
            modifiers["sort"] = SortQueryModyfier()
        if self.enable_slice:
            modifiers["slice"] = SliceQueryModifier()
        return modifiers

    def create_modifiers_for_list(self):
        modifiers = self.create_empty_qmethods()
        if self.enable_filter:
            modifiers["filter"] = FilterListModifier(
                operators=self.filter_operators,
                columns=self.filter_columns,
                overrides=self.filter_overrides
            )
        if self.enable_sort:
            modifiers["sort"] = SortListModyfier()
        if self.enable_slice:
            modifiers["slice"] = SliceListModifier()
        return modifiers  

    def create_empty_qmethods(self):
        empty_qmethod = lambda x, *args, **kwargs: x
        return dict(
            filter=empty_qmethod,
            sort=empty_qmethod,
            slice=empty_qmethod
        )


class SerializerMixin(object):
    schema = None
    schema_post = None

    def get_schema(self, fields=None):
        if request.method in ("GET", "HEAD"):
            schema = self.schema(only=fields)
        else:
            schema = (self.schema_post or self.schema)()
        return schema

    def serialize_objects(self, objs, many=False, fields=None):
        schema = self.get_schema(fields)
        data = schema.dump(objs, many=many).data
        return data


class ListView(
    QueryStringParserMixin, QueryParametersMixin, SerializerMixin, 
    MethodView
):
    parser = FlaskRequestParamsReader()
    model = None

    @auth.login_required
    @permission_required(Permission.BROWSE_DATA)
    def get(self, *args, **kwargs):
        params = self.get_query_params()
        objs = self.get_objects(params, *args, **kwargs)
        data = self.serialize_objects(objs, many=True, fields=params["fields"])
        return self.create_json_response(data)
        
    def get_objects(self, params, *args, **kwargs):
        query = self.apply_query_parameters(
            self.get_query(*args, **kwargs), params
        )
        objs = self.execute_query(query)
        return objs
        
    def get_query(self, *args, **kwargs):
        query = db.session.query(self.model)
        return query

    def execute_query(self, query):
        if isinstance(query, Query):
            return query.all()
        else:
            return query

    def create_json_response(self, data):
        return jsonify({
            "results": data,
            "count": len(data)
        }), 200
    
    post = create_http_request_handler("create")
    delete = create_http_request_handler("delete")
    put = create_http_request_handler("update")
    
    def create_dbrequests(self, action, user, **kwargs):
        request_data = json.loads(request.data.decode())
        many = request.args.get("many", "F").lower() in ("t", "true")
        if not many: # change request_data into iterable
            request_data = (request_data,)
        
        dbrequests = list()
        for data in request_data:
            data.update(kwargs)
            data = self.modify_data(data)
            dbrequests.append(
                DBRequest(data=json.dumps(data), user=user, action=action, 
                          model=self.model.__name__)
            )
        return dbrequests

    def modify_data(self, data):
        return data


class DetailView(QueryStringParserMixin, SerializerMixin, MethodView):
    parser = FlaskRequestParamsReader()
    model = None

    @auth.login_required
    @permission_required(Permission.BROWSE_DATA)
    def get(self, *args, **kwargs):
        params = self.get_query_params()
        obj = self.get_object(*args, **kwargs)
        data = self.serialize_objects(
            obj, many=False, fields=params.get("fields", None)
        )
        return jsonify(data), 200

    @auth.login_required
    @permission_required(Permission.CREATE_REQUESTS)
    def delete(self, *args, **kwargs):
        obj = self.get_object(*args, **kwargs)
        dbrequest = self.create_dbrequest("delete", g.user, **kwargs)
        db.session.add(dbrequest)
        db.session.commit()
        return jsonify({}), 202

    @auth.login_required
    @permission_required(Permission.CREATE_REQUESTS)
    def put(self, *args, **kwargs):
        obj = self.get_object(*args, **kwargs)
        dbrequest = self.create_dbrequest("update", g.user, **kwargs)
        db.session.add(dbrequest)
        db.session.commit()
        return jsonify({}), 202   

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

    def modify_data(self, data):
        return data

    def get_object(self, id):
        obj = db.session.query(self.model).get(id)
        if not obj:
            abort(404)
        return obj