from collections import namedtuple
import json
import re
import operator

from sqlalchemy.orm.query import Query
from flask import request, current_app

import db.utils as dbutil
import rparser.utils as putil
from rparser.core import FinancialReport

#-------------------------------------------------------------------------------
# Filtering With Query Parameters
#-------------------------------------------------------------------------------

class QueryFilter:
    '''
    Represent relation between operator and method that implments logic of the 
    operator.
    '''
    REGEX_SPECIAL_CHARACTERS = "\\^${}[]().*+?|<>-&"

    def __init__(self, operator, method):
        self.method = method
        self.operator = operator
        self.regex = self._create_regex(operator)

    def _create_regex(self, operator):
        chars = list()
        for char in operator:
            if char in self.REGEX_SPECIAL_CHARACTERS:
                chars.append("\\%s" % char)
            else:
                chars.append(char)
        re_expr = "^(?P<column>[^=\<\>!]+)%s(?P<value>.*)" % "".join(chars)
        return re.compile(re_expr)

    def __call__(self, obj, expr):
        m = re.match(self.regex, expr)
        try:
            subject = getattr(obj, m.group("column"))
            value = m.group("value")
        except (AttributeError, IndexError):
            return None
        else:
            return self.method(subject, value) 

    def match(self, expr):
        return re.match(self.regex, expr)


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


sql_query_filters = [
    QueryFilter(operator="=", method=operator.eq),
    QueryFilter(operator="<=", method=operator.le),
    QueryFilter(operator="<", method=operator.lt),
    QueryFilter(operator="!=", method=operator.ne),
    QueryFilter(operator=">=", method=operator.ge),
    QueryFilter(operator=">", method=operator.gt),
    QueryFilter(operator="@in@", method=lambda c, v: c.in_(v.split(",")))
]

qlist_filters = [
    QueryFilter(operator="=", method=apply_conversion(operator.eq)),
    QueryFilter(operator="<=", method=apply_conversion(operator.le)),
    QueryFilter(operator="<", method=apply_conversion(operator.lt)),
    QueryFilter(operator="!=", method=apply_conversion(operator.ne)),
    QueryFilter(operator=">=", method=apply_conversion(operator.ge)),
    QueryFilter(operator=">", method=apply_conversion(operator.gt)),
    QueryFilter(operator="@in@", method=qlist_in_operator)
]


def create_query_filter(model, expr):
    try:
        qfilter = next(qf for qf in sql_query_filters if qf.match(expr))
    except StopIteration:
        return True

    return qfilter(model, expr)


def filter_query_list(qlist, expr):
    try:
        qfilter = next(qf for qf in qlist_filters if qf.match(expr))
    except StopIteration:
        return qlist

    new_qlist = [ item for item in qlist if qfilter(item, expr) ]
    return new_qlist


def get_models_from_query(query):
    return [ mapper.type for mapper in query._mapper_entities ]


def apply_query_parameters_to_list(qlist, filters, limit, offset, sort):
    if filters:
        for expr in filters:
            qlist = filter_query_list(qlist, expr)

    if sort:
        for field in sort.split(","):
            index = 1 if field.startswith("-") else 0
            try:
                qlist = sorted(
                    qlist, key=lambda x: getattr(x, field[index:]),
                    reverse = bool(index)
                )
            except AttributeError:
                continue
    if not limit: limit = len(qlist)
    qlist = qlist[offset:(offset+limit)]
    return qlist


def apply_query_parameters_to_query(query, filters, limit, offset, sort):
    if filters:
        model = get_models_from_query(query)[0]
        for expr in filters:
            query = query.filter(create_query_filter(model, expr))

    if sort:
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
    
    query = query.limit(limit or None).offset(offset or None)
    return query.all()


def apply_query_parameters(obj):
    filters = request.args.get("filter", None)
    if filters: filters = filters.split(";")
    limit = int(request.args.get("limit", 0))
    offset = int(request.args.get("offset", 0))
    sort = request.args.get("sort")
    if sort: sort = "".join(sort.split()) # remove all whitespaces

    if isinstance(obj, Query):
        method = apply_query_parameters_to_query
    else:
        method = apply_query_parameters_to_list

    return method(obj, filters, limit, offset, sort)

#-------------------------------------------------------------------------------