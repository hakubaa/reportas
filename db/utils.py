from collections import namedtuple
from functools import reduce
import operator


FiscalYear = namedtuple("FiscalYear", field_names="start, end")
TimeRange = namedtuple("TimeRange", field_names="start, end")


def group_objects(objs, key):
    result = dict()
    for obj in objs:
        result.setdefault(key(obj), []).append(obj)
    return result
    

def concatenate_lists(lists):
    return reduce(lambda list_1, list_2: list_1 + list_2, lists)
    


class Formula:
    
    class Component:
    
        def __init__(self, rtype, sign):
            self.rtype = rtype
            self.sign = sign

        def __hash__(self):
            return hash(self.rtype) ^ hash(self.sign)

        def __eq__(self, other):
            if self.rtype != other.rtype or self.sign != other.sign:
                return False
            return True
        
        def calculate(self, data):
            return self.sign * self.get_value(data)
        
        def is_calculable(self, data):
            try:
                self.get_value(data)
                return True
            except KeyError:
                return False
        
        def get_value(self, data):
            return data[self.rtype]
    
    class TimeRangeComponent(Component):
        
        def __init__(self, rtype, sign, timerange):
            super().__init__(rtype, sign)
            self.timerange = timerange
    
        def __hash__(self):
            return hash(self.rtype) ^ hash(self.sign) ^ hash(self.timerange)

        def __eq__(self, other):
            if self.rtype != other.rtype or self.sign != other.sign \
                   or self.timerange != other.timerange:
                return False
            return True

        def get_value(self, data):
            return data[self.rtype][self.timerange]
    
    
    def __init__(self, lhs, rhs=None):
        self.lhs = lhs
        self.rhs = rhs or list()
    
    def __hash__(self):
        return hash(self.lhs) ^ reduce(operator.xor, map(hash, self.rhs))   

    def __eq__(self, other):
        if self.lhs != other.lhs:
            return False
        if len(self.rhs) != len(other.rhs):
            return False
        for c1, c2 in zip(self.rhs, other.rhs):
            if c1 != c2:
                return False
        return True

    def __iter__(self):
        return iter(self.rhs)

    def __len__(self):
        return len(self.rhs)

    def add_component(self, component):
        self.rhs.append(component)
    
    def calculate(self, data):
        return sum(item.calculate(data) for item in self)
    
    def is_calculable(self, data):
        return all(map(lambda item: item.is_calculable(data), self))
    
    def extend_with_timerange(self, timerange):
        new_formula = Formula(
            Formula.TimeRangeComponent(self.lhs.rtype, 0, timerange)
        )
        for item in self:
            new_formula.add_component(
                Formula.TimeRangeComponent(item.rtype, item.sign, timerange)
            )
        return new_formula


def convert_db_formula(formula):
    new_formula = Formula(Formula.Component(formula.rtype, 0))
    for item in formula.rhs:
        new_formula.add_component(Formula.Component(item.rtype, item.sign))
    return new_formula


def create_timerange_formula(rtype, lhs_spec, rhs_spec):
    formula = Formula(
        Formula.TimeRangeComponent(rtype, lhs_spec[1], lhs_spec[0])
    )
    for spec in rhs_spec:
        formula.add_component(
            Formula.TimeRangeComponent(rtype, spec[1], spec[0])
        )
    return formula  


def create_formulas_for_csr(formulas):
    pass