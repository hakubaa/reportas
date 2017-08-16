from collections import namedtuple
import collections
from functools import reduce
import operator
from datetime import date, timedelta


FiscalYear = namedtuple("FiscalYear", field_names="start, end")
TimeRange = namedtuple("TimeRange", field_names="start, end")


def group_objects(objs, key):
    result = dict()
    for obj in objs:
        result.setdefault(key(obj), []).append(obj)
    return result
    

def concatenate_lists(lists):
    return reduce(lambda list_1, list_2: list_1 + list_2, lists, [])
    

def create_formulas_for_csr(
    base_formulas, timeranges=None, timerange_formulas=None, rtypes=None
):
    if not isinstance(base_formulas, collections.Iterable):
        base_formulas = [base_formulas]
    formulas = list(base_formulas)
    formulas.extend(create_db_formulas_transformations(formulas))
    formulas = convert_db_formulas(formulas)
    formulas = extend_formulas_with_timerange(formulas, timeranges)
    if timerange_formulas and rtypes:
        formulas.extend(create_timerange_formulas(rtypes, timerange_formulas))
    formulas = remove_duplicated_formulas(formulas)
    return formulas


def project_timerange_onto_fiscal_year(timerange, fiscal_year):
    start_month = fiscal_year.start.month + timerange.start - 1
    if start_month > 12:
        start_month -= 12
        start_year = fiscal_year.start.year + 1
    else:
        start_year = fiscal_year.start.year
    start_timestamp = date(start_year, start_month, 1)
    
    end_month = fiscal_year.start.month + timerange.end - 1
    if end_month > 12:
        end_month -= 12
        end_year = fiscal_year.start.year + 1
    else:
        end_year = fiscal_year.start.year

    if end_month == 12:
        end_timestamp = date(end_year+1, 1, 1) - timedelta(days=1)    
    else:
        end_timestamp = date(end_year, end_month+1, 1) - timedelta(days=1)
    
    return TimeRange(start=start_timestamp, end=end_timestamp)