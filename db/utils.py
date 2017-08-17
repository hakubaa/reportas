from collections import namedtuple
from functools import reduce


FiscalYear = namedtuple("FiscalYear", field_names="start, end")


def group_objects(objs, key):
    result = dict()
    for obj in objs:
        result.setdefault(key(obj), []).append(obj)
    return result
    

def concatenate_lists(lists):
    return reduce(lambda list_1, list_2: list_1 + list_2, lists, [])