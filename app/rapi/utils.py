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
        re_expr = "^(?P<column>[^=\<\>!]+)%s(?P<value>.*)" % "".join(chars)
        return re.compile(re_expr)

    def __call__(self, obj, expr):
        m = re.match(self.regex, expr)
        try:
            subject = getattr(obj, m.group("column"))
            value = m.group("value")
        except (AttributeError, IndexError):
            return None
        
        if self.is_model(obj):
            return self.method_query(subject, value) 
        else:
            return self.method_list(subject, value)

    def is_model(self, cls):
        try:
            class_mapper(cls)
        except:
            return False
        return True

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


class FilterParser:
    REGEX_FILTER = "^(?P<field>[^=\<\>!]+)(?P<operator>.*)(?P<value>.*)"
    
    def __init__(self, expr):
        self.expr = re.match(self.REGEX_FILTER, expr)
        
    @property
    def field(self):
        return self.expr.group("field")
        
    @property
    def operator(self):
        return self.expr.group("operator")
        
    @property
    def value(self):
        return self.expr.group("value")