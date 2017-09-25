import json
import operator

from flask import jsonify, request, g, abort
from flask.views import MethodView
from sqlalchemy.orm.query import Query

from app.rapi.utils import QueryFilter, apply_conversion, qlist_in_operator
from app.models import DBRequest, Permission
from app.user import auth
from app.user.auth import permission_required
from app import db


class ViewUtilMixin(object):
    schema = None
    schema_post = None

    def get_schema(self, *args, **kwargs):
        if request.method in ("GET", "HEAD"):
            fields = request.values.get("fields", None)
            if fields: fields = "".join(fields.split()).split(",")
            schema = self.schema(only=fields)
        else:
            schema = (self.schema_post or self.schema)(*args, **kwargs)
        return schema

    def modify_data(self, data):
        return data


def create_http_request_handler(action, permissions=Permission.CREATE_REQUESTS):
    '''Factory of methods to handle http requests (used in ListView).'''
    def http_method(self, *args, **kwargs):
        dbrequests = self.create_dbrequests(action, g.user, **kwargs)
        db.session.add_all(dbrequests)
        db.session.commit()
        return jsonify({}), 202
    return auth.login_required(permission_required(permissions)(http_method))


class DetailView(ViewUtilMixin, MethodView):
    model = None

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

    def get_object(self, id):
        obj = db.session.query(self.model).get(id)
        if not obj:
            abort(404)
        return obj

    @auth.login_required
    @permission_required(Permission.BROWSE_DATA)
    def get(self, *args, **kwargs):
        obj = self.get_object(*args, **kwargs)
        schema = self.get_schema()
        data = schema.dump(obj).data
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


class ListView(ViewUtilMixin, MethodView):
    model = None

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

    @auth.login_required
    @permission_required(Permission.BROWSE_DATA)
    def get(self, *args, **kwargs):
        query = self.apply_query_parameters(self.get_query(*args, **kwargs))
        objs = self.execute_query(query)
        schema = self.get_schema()
        data = schema.dump(objs, many=True).data
        return jsonify({
            "results": data,
            "count": len(data)
        }), 200

    def get_query(self, *args, **kwargs):
        return self.get_objects(*args, **kwargs)
        
    def get_objects(self, *args, **kwargs):
        objs = db.session.query(self.model)
        return objs
        
    def execute_query(self, query):
        if isinstance(query, Query):
            return query.all()
        else:
            return query
        
    def apply_query_parameters(self, query):
        if isinstance(query, Query):
            method = self.apply_query_parameters_to_query
        else:
            method = self.apply_query_parameters_to_list
            
        qparams = self.get_query_parameters()
        return method(query, **qparams)
        
    def get_query_parameters(self):
        filters = request.args.get("filter", [])
        if isinstance(filters, str): filters = filters.split(";")
        limit = int(request.args.get("limit", 0))
        offset = int(request.args.get("offset", 0))
        sort = request.args.get("sort")
        if sort: sort = "".join(sort.split()) # remove all whitespaces
        
        return {
            "filters": filters, "sort": sort,
            "limit": limit, "offset": offset
        }
        
    def apply_query_parameters_to_query(self, query, filters, limit, offset, sort):
        query = self.apply_filters_to_query(query, filters)
        query = self.apply_sort_to_query(query, sort)
        query = self.apply_slice_to_query(query, limit, offset)
        return query.all()
        
    def apply_filters_to_query(self, query, filters):
        model = self.get_models_from_query(query)[0]
        for expr in filters:
            query = self.apply_filter_to_query(query, expr, model)
        return query
        
    def apply_filter_to_query(self, query, expr, model):
        qfilter = self.match_filter(expr)
        if not qfilter:
            return query
        else:
            return query.filter(qfilter(model, expr))

    def match_filter(self, expr):
        try:
            qfilter = next(qf for qf in self.get_filters(expr) if qf.match(expr))
        except StopIteration:
            return None
        else:
            return qfilter
            
    def get_filters(self, expr):
        field = QueryFilter.identify_field(expr)
        if not (field and self.is_field_eligible_for_filtering(field)):
            return []
        filters = self.filter_overrides.get(field, self.filter_operators)
        return filters
            
    def is_field_eligible_for_filtering(self, field):
        if len(self.filter_columns) > 0 and not field in self.filter_columns:
            return False
        return True
        
    def apply_sort_to_query(self, query, sort):
        if not sort:
            return query
            
        for field in sort.split(","):
            index = 1 if field.startswith("-") else 0
            try:
                model = query.column_descriptions[0]["type"]
                column = model.__table__.columns[field[index:]]
                if index:
                    column = column.desc()
            except KeyError:
                continue
            else:
                query = query.order_by(column)
                
        return query
                    
    def apply_slice_to_query(self, query, limit, offset):
        return query.limit(limit or None).offset(offset or None)

    def apply_query_parameters_to_list(self, qlist, filters, limit, offset, sort):
        qlist = self.apply_filters_to_list(qlist, filters)
        qlist = self.apply_sort_to_list(qlist, sort)
        qlist = self.apply_slice_to_list(qlist, limit, offset)
        return qlist
        
    def apply_filters_to_list(self, qlist, filters):
        for expr in filters:
            qlist = self.apply_filter_to_list(qlist, expr)
        return qlist

    def apply_filter_to_list(self, qlist, expr):
        qfilter = self.match_filter(expr)
        if not qfilter:
            return qlist
        else:
            return [ item for item in qlist if qfilter(item, expr) ]
        
    def apply_sort_to_list(self, qlist, sort):
        if not sort:
            return qlist
            
        for field in sort.split(","):
            index = 1 if field.startswith("-") else 0
            try:
                qlist = sorted(
                    qlist, key=lambda x: getattr(x, field[index:]),
                    reverse = bool(index)
                )
            except AttributeError:
                continue
            
        return qlist
        
    def apply_slice_to_list(self, qlist, limit, offset):
        if not limit: limit = len(qlist)
        qlist = qlist[offset:(offset+limit)]
        return qlist

    def get_models_from_query(self, query):
        return [ mapper.type for mapper in query._mapper_entities ]
    
    
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