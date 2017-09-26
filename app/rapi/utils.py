from collections import namedtuple
import json
import re
import operator

from sqlalchemy.orm.query import Query
from sqlalchemy.orm.util import class_mapper
from flask import request, current_app

import db.utils as dbutil
import rparser.utils as putil
from rparser.core import FinancialReport


class QueryFilter:
    '''
    Represent relation between operator and method that implments logic of the 
    operator.
    '''
    REGEX_SPECIAL_CHARACTERS = "\\^${}[]().*+?|<>-&"
    REGEX_EXPR = "^(?P<column>[^=\<\>!@]+){}(?P<value>.*)"

    def __init__(self, operator, method_query, method_list=None):
        self.method_query = method_query
        self.method_list = method_list
        self.operator = operator
        self.regex = self._create_regex(operator)

    def _create_regex(self, operator):
        chars = list()
        for char in operator:
            if char in self.REGEX_SPECIAL_CHARACTERS:
                chars.append("\\%s" % char)
            else:
                chars.append(char)
        re_expr = self.REGEX_EXPR.format("".join(chars))
        return re.compile(re_expr)

    def __call__(self, obj, expr):
        params = self.parse_expr(expr)
        if not params:
            return None
            
        params_for_method = (
            getattr(obj, self.modify_column(params["column"])),
            self.modify_value(params["value"])
        )
        if self.is_model(obj):
            return self.method_query(*params_for_method) 
        else:
            return (self.method_list or self.method_query)(*params_for_method)
            
    def modify_column(self, column):
        return column
        
    def modify_value(self, value):
        return value

    def parse_expr(self, expr):
        m = re.match(self.regex, expr)
        try:
            column = m.group("column")
            value = m.group("value")
        except AttributeError:
            return None
        else:
            return dict(column=column, value=value)
        
    def is_model(self, cls):
        try:
            class_mapper(cls)
        except:
            return False
        return True

    def match(self, expr):
        return re.match(self.regex, expr)
        
    @classmethod
    def identify_field(cls, expr):
        re_expr = re.compile(cls.REGEX_EXPR.format(".*"))
        m = re.match(re_expr, expr)
        if not m:
            return None
        return m.group("column")


class FlaskRequestParamsReader:

    def get_params(self):
        params = dict()
        params["filter"] = self.get_filter_params()
        params["sort"] = self.get_sort_params()
        params["fields"] = self.get_fields_params()
        params.update(self.get_slice_params())
        return params

    def get_filter_params(self, sep=";"):
        filters = request.args.get("filter", "")
        return self.split_and_remove_false_items(filters, sep)

    def get_slice_params(self):
        limit = self.convert_to_int(request.args.get("limit", None))
        offset = self.convert_to_int(request.args.get("offset", None))
        return dict(limit=limit, offset=offset)

    def get_sort_params(self, sep=","):
        sort_query = self.remove_white_spaces(request.args.get("sort", ""))
        return self.split_and_remove_false_items(sort_query, sep)

    def get_fields_params(self, sep=","):
        fields = self.remove_white_spaces(request.args.get("fields", ""))
        return self.split_and_remove_false_items(fields, sep)

    def get_many_params(self):
        many = request.args.get("many", "False")
        return many.upper() in ("T", "TRUE", "Y", "YES")

    def convert_to_int(self, string):
        if string is not None:
            string = int(string)
        return string

    def remove_white_spaces(self, string):
        return "".join(string.split())

    def split_and_remove_false_items(self, string, sep):
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
        return self.apply(query, limit, offset)
    
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
        return self.apply(items, limit, offset)
    
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


def qlist_in_operator(value, strlist):
    value_type = type(value)
    values = [ value_type(item) for item in strlist.split(",") ]
    return value in values


def apply_conversion(f):
    def wrapper(c, v):
        type_c = type(c)
        value = type_c(v)
        return f(c, value)
    return wrapper 