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

#-------------------------------------------------------------------------------
# Filtering With Query Parameters
#-------------------------------------------------------------------------------

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
            return self.method_list(*params_for_method)
            
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