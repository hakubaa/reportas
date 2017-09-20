from collections import namedtuple
from functools import reduce
import calendar
import datetime


FiscalYear = namedtuple("FiscalYear", field_names="start, end")


def group_objects(objs, key):
    result = dict()
    for obj in objs:
        result.setdefault(key(obj), []).append(obj)
    return result
    

def concatenate_lists(lists):
    return reduce(lambda list_1, list_2: list_1 + list_2, lists, [])


def datesrange(start_date, end_date, delta):
    curr_date = start_date
    while curr_date <= end_date:
        yield curr_date
        curr_date = end_of_month(curr_date, delta)


def end_of_month(date, months_to_add=0):
    year = date.year
    month = date.month + months_to_add
    if month > 12:
        year += 1
        month = month - 12
    return datetime.date(year, month, calendar.monthrange(year, month)[1])


def determine_fiscal_months(fy_start_month, timerange):
    months = list()
    next_month = fy_start_month - 1 or 12

    while next_month not in months:
        months.append(next_month)
        next_month += timerange
        if next_month > 12:
            next_month = next_month - 12

    return months