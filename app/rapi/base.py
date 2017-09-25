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


class FlaskRequestParamsReader:

    def get_params(self):
        params = dict()
        params["filter"] = self.get_filter_params()
        params["sort"] = self.get_sort_params()
        params.update(self.get_slice_params())
        return params

    def get_filter_params(self, sep=";"):
        filters = request.args.get("filter", "")
        return self._split_and_remove_false_items(filters, sep)

    def get_slice_params(self):
        limit = int(request.args.get("limit", None))
        offset = int(request.args.get("offset", None))
        return dict(limit=limit, offset=offset)

    def get_sort_params(self, sep=","):
        sort_query = self._remove_white_spaces(request.args.get("sort", ""))
        return self._split_and_remove_false_items(sort_query, sep)

    def _remove_white_spaces(self, string):
        return "".join(string.split())

    def _split_and_remove_false_items(self, string, sep):
        return list(filter(bool, string.split(sep)))


class SortQueryModyfier(object):

    def __call__(self, query, fields):
        return self.apply(query, fields)

    def apply(self, query, fields):
        for field in fields:
            query = self.apply_order(query, field)
        return query

    def apply_order(self, query, field):
        model = self.get_model(query)
        column = self.get_column(model, field)
        if column is None:
            return query
        if self.is_descending_sort(field):
            column = column.desc()
        query = query.order_by(column)
        return query     

    def get_model(self, query):
        return query.column_descriptions[0]["type"]

    def get_column(self, model, field):
        index = 1 if self.is_descending_sort(field) else 0
        try:
            column = model.__table__.columns[field[index:]]
        except KeyError:
            return None
        else:
            return column

    def is_descending_sort(self, field):
        return field.startswith("-")


class SliceQueryModifier(object):

    def __call__(self, query, limit=None, offset=None):
        return self.apply(query, params)
    
    def apply(self, query, limit=None, offset=None):
        query = self.apply_limit_to_query(query, limit)
        query = self.apply_offset_to_query(query, offset)
        return query

    def apply_limit_to_query(self, query, limit):
        return query.limit(limit)

    def apply_offset_to_query(self, query, offset):
        return query.offset(offset)


class QueryModifierMixin(object):

    def match_filter(self, expr):
        try:
            qfilter = next(x for x in self.get_filters(expr) if x.match(expr))
        except StopIteration:
            return None
        else:
            return qfilter
            
    def get_filters(self, expr):
        field = self.get_field_from_expr(expr)
        if not (field and self.is_field_eligible_for_filtering(field)):
            return []
        filters = self.overrides.get(field, self.operators)
        return filters
    
    def get_field_from_expr(self, expr):
        return QueryFilter.identify_field(expr)

    def is_field_eligible_for_filtering(self, field):
        if len(self.columns) > 0 and not field in self.columns:
            return False
        return True  


class FilterQueryModifier(QueryModifierMixin):

    def __init__(self, operators, columns=list(), overrides=dict()):
        self.operators = operators
        self.columns = columns
        self.overrides = overrides

    def __call__(self, query, params):
        return self.apply(query, params)
    
    def apply(self, query, params):
        query = self.apply_filters_to_query(query, params)
        return query

    def apply_filters_to_query(self, query, filters):
        for expr in filters:
            if not self.is_valid_expr(query, expr):
                continue
            query = self.apply_filter_to_query(query, expr)
        return query
        
    def apply_filter_to_query(self, query, expr):
        qfilter = self.match_filter(expr)
        if not qfilter:
            return query
        else:
            model = self.get_model(query)
            return query.filter(qfilter(model, expr))

    def is_valid_expr(self, query, expr):
        model = self.get_model(query)
        field = self.get_field_from_expr(expr)
        try:
            model.__table__.columns[field]
        except KeyError:
            return False
        else:
            return True

    def get_model(self, query):
        return query.column_descriptions[0]["type"]


class SortListModyfier(object):

    def __call__(self, query, params):
        return self.apply(query, params)

    def apply(self, items, fields):
        for field in fields:
            items = self.apply_order(items, field)
        return items

    def apply_order(self, items, field):
        index = 1 if self.is_descending_sort(field) else 0
        try:
            items = sorted(
                items, key=lambda x: getattr(x, field[index:]),
                reverse = bool(index)
            )
        except AttributeError:
            pass
        
        return items

    def is_descending_sort(self, field):
        return field.startswith("-")


class SliceListModifier(object):

    def __call__(self, items, limit=None, offset=None):
        return self.apply(items, params)
    
    def apply(self, items, limit=None, offset=None):
        if limit is None: 
            limit = len(items)
        if offset is None:
            offset = 0
        return items[offset:(offset+limit)]


class FilterListModifier(QueryModifierMixin):

    def __init__(self, operators, columns=list(), overrides=dict()):
        self.operators = operators
        self.columns = columns
        self.overrides = overrides

    def __call__(self, items, params):
        return self.apply(items, params)

    def apply(self, items, filters):
        for expr in filters:
            if not self.is_valid_expr(items, expr):
                continue
            items = self.apply_filter_to_list(items, expr)
        return items

    def apply_filter_to_list(self, items, expr):
        qfilter = self.match_filter(expr)
        if not qfilter:
            return items
        else:
            return [ item for item in items if qfilter(item, expr) ]

    def is_valid_expr(self, items, expr):
        field = self.get_field_from_expr(expr)
        try:
            list(map(operator.attrgetter(field), items))
        except AttributeError:
            return False
        else:
            return True


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
            qmethos = self.create_qmethos_for_query() 
        else:
            qmethos = self.create_qmethos_for_list()

        obj = qmethos["filter"](obj, params["filter"])
        obj = qmethos["sort"](obj, params["sort"])
        obj = qmethos["slice"](obj, params["limit"], params["offset"])

        return obj

    def create_qmethos_for_query(self):
        qmethos = self.create_empty_qmethods()
        if self.enable_filter:
            qmethos["filter"] = FilterQueryModifier(
                operators=self.filter_operators,
                columns=self.filter_columns,
                overrides=self.filter_overrides
            )
        if self.enable_sort:
            qmethos["sort"] = SortQueryModyfier()
        if self.enable_slice:
            qmethos["slice"] = SliceQueryModifier()
        return qmethods

    def create_qmethods_for_list(self):
        qmethos = self.create_empty_qmethods()
        if self.enable_filter:
            qmethos["filter"] = FilterListModifier(
                operators=self.filter_operators,
                columns=self.filter_columns,
                overrides=self.filter_overrides
            )
        if self.enable_sort:
            qmethos["sort"] = SortListModyfier()
        if self.enable_slice:
            qmethos["slice"] = SliceListModifier()
        return qmethods  

    def create_empty_qmethods(self):
        empty_qmethod = lambda x, *args, **kwargs: x
        return dict(
            filter=empty_qmethod,
            sort=empty_qmethod,
            slice=empty_qmethod
        )


class ListView(QueryParametersMixin, ViewUtilMixin, MethodView):
    model = None

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