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
    
    
def represent_records_as_matrix(records, fiscal_year=None):
    matrix = dict()
    for record in records:
        timerange = record.project_onto_fiscal_year(fiscal_year)
        matrix.setdefault(record.rtype, dict()).update({timerange: record.value})
    return matrix
    
#-------------------------------------------------------------------------------
# Utils for formulas
#-------------------------------------------------------------------------------

class Formula:

    TIMERANGES_POT = [ # pot - period of time
        # 3-month length timeranges
        TimeRange(1, 3),
        TimeRange(4, 6),
        TimeRange(7, 9),
        TimeRange(10, 12),
        # 6-month length timeranges
        TimeRange(1, 6),
        TimeRange(7, 12),
        # 9-month length timeranges
        TimeRange(1, 9),
        # 12-month length timeranges
        TimeRange(1, 12)
    ]

    TIMERANGES_PIT = [ #pit - point in time
        # the end month of quarter
        TimeRange(3, 3),
        TimeRange(6, 6),
        TimeRange(9, 9),
        TimeRange(12, 12)
    ]
    
    TIMERANGE_FORMULAS_SPEC = [
        ((0, TimeRange(1, 3)), [(1, TimeRange(1, 6)), (-1, TimeRange(4, 6))]),
        ((0, TimeRange(1, 3)), [(1, TimeRange(1, 9)), (-1, TimeRange(4, 9))]),
        ((0, TimeRange(1, 3)), [(1, TimeRange(1, 9)), (-1, TimeRange(4, 6)), (-1, TimeRange(7, 9))]),
        ((0, TimeRange(1, 3)), [(1, TimeRange(1, 12)), (-1, TimeRange(4, 12))]),
        ((0, TimeRange(1, 3)), [(1, TimeRange(1, 12)), (-1, TimeRange(4, 6)), (-1, TimeRange(7, 9)), (-1, TimeRange(10, 12))]),
        
        ((0, TimeRange(4, 6)), [(1, TimeRange(1, 6)), (-1, TimeRange(1, 3))]),
        ((0, TimeRange(4, 6)), [(1, TimeRange(1, 9)), (-1, TimeRange(1, 3)), (-1, TimeRange(7, 9))]),
        ((0, TimeRange(4, 6)), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 3)), (-1, TimeRange(7, 9)), (-1, TimeRange(10, 12))]),
        ((0, TimeRange(4, 6)), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 3)), (-1, TimeRange(7, 12))]),
        
        ((0, TimeRange(7, 9)), [(1, TimeRange(1, 9)), (-1, TimeRange(1, 6))]),
        ((0, TimeRange(7, 9)), [(1, TimeRange(1, 9)), (-1, TimeRange(1, 3)), (-1, TimeRange(4, 6))]),
        ((0, TimeRange(7, 9)), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 6)), (-1, TimeRange(10, 12))]),
        ((0, TimeRange(7, 9)), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 3)), (-1, TimeRange(4, 6)), (-1, TimeRange(10, 12))]),
       
        ((0, TimeRange(10, 12)), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 3)), (-1, TimeRange(4, 6)), (-1, TimeRange(7, 9))]),
        ((0, TimeRange(10, 12)), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 9))]),
        ((0, TimeRange(10, 12)), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 6)), (-1, TimeRange(7, 9))]),
        ((0, TimeRange(10, 12)), [(1, TimeRange(7, 12)), (-1, TimeRange(7, 9))]),
        
        ((0, TimeRange(1, 6)), [(1, TimeRange(1, 3)), (1, TimeRange(4, 6))]),
        ((0, TimeRange(1, 6)), [(1, TimeRange(1, 12)), (-1, TimeRange(7, 12))]),
        ((0, TimeRange(1, 6)), [(1, TimeRange(1, 9)), (-1, TimeRange(7, 9))]),
        
        ((0, TimeRange(7, 12)), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 6))]),
        ((0, TimeRange(7, 12)), [(1, TimeRange(1, 12)), (-1, TimeRange(1, 3)), (-1, TimeRange(4, 6))]),
        ((0, TimeRange(7, 12)), [(1,TimeRange (7, 9)), (1, TimeRange(10, 12))]),
        
        ((0, TimeRange(1, 9)), [(1, TimeRange(1, 3)), (1, TimeRange(4, 6)), (1, TimeRange(7, 9))]),
        ((0, TimeRange(1, 9)), [(1, TimeRange(1, 12)), (-1, TimeRange(10, 12))]),
        ((0, TimeRange(1, 9)), [(1, TimeRange(1, 6)), (1, TimeRange(7, 9))]),
        ((0, TimeRange(1, 9)), [(1, TimeRange(1, 3)), (1, TimeRange(4, 9))]),
        
        ((0, TimeRange(1, 12)), [(1, TimeRange(1, 3)), (1, TimeRange(4, 6)), (1, TimeRange(7, 9)), (1, TimeRange(10, 12))]),
        ((0, TimeRange(1, 12)), [(1, TimeRange(1, 6)), (1, TimeRange(7, 12))]),
        ((0, TimeRange(1, 12)), [(1, TimeRange(1, 9)), (1, TimeRange(10, 12))])
    ]
    
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
        
    def is_calculated(self, data):
        try:
            self.lhs.get_value(data)
            return True
        except KeyError:
            return False

    @classmethod
    def create_pot_formulas(cls, db_formulas, rtypes=None):
        return create_formulas_for_csr(
            db_formulas,
            timeranges=cls.TIMERANGES_POT,
            timerange_formulas=cls.TIMERANGE_FORMULAS_SPEC,
            rtypes=rtypes
        )

    @classmethod
    def create_pit_formulas(cls, db_formulas):
        return create_formulas_for_csr(
            db_formulas,
            timeranges=cls.TIMERANGES_PIT
        )


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
    

def create_db_formulas_transformations(formulas):
    if not isinstance(formulas, collections.Iterable):
        formulas = [formulas]
    new_formulas = list()
    for formula in formulas:
        rhs_rtypes = map(lambda item: item.rtype, formula.rhs)
        new_formulas.extend(formula.transform(rtype) for rtype in rhs_rtypes)
    return new_formulas
    

def convert_db_formulas(formulas):
    return [ convert_db_formula(formula) for formula in formulas ]
    
    
def convert_db_formula(formula):
    new_formula = Formula(Formula.Component(formula.rtype, 0))
    for item in formula.rhs:
        new_formula.add_component(Formula.Component(item.rtype, item.sign))
    return new_formula


def extend_formulas_with_timerange(formulas, timerange_spec):
    if not isinstance(formulas, collections.Iterable):
        formulas = [formulas]

    return [ 
        formula.extend_with_timerange(timerange) 
        for formula in formulas
        for timerange in timerange_spec 
    ]


def create_timerange_formulas(rtypes, timerange_formulas):
    formulas = list()
    for rtype in rtypes:
        formulas.extend(
            create_timerange_formula(rtype, lhs_spec, rhs_spec)
            for lhs_spec, rhs_spec in timerange_formulas
        )
    return formulas


def create_timerange_formula(rtype, lhs_spec, rhs_spec):
    formula = Formula(
        Formula.TimeRangeComponent(
            rtype, timerange=lhs_spec[1], sign=lhs_spec[0]
        )
    )
    for spec in rhs_spec:
        formula.add_component(
            Formula.TimeRangeComponent(
                rtype, timerange=spec[1], sign=spec[0]
            )
        )
    return formula  


def remove_duplicated_formulas(formulas):
    return list(set(formulas))
    

def create_inverted_mapping(formulas):
    mapping = dict()
    for formula in formulas:
        for item in formula:
            mapping.setdefault(item.rtype, dict()).\
                    setdefault(item.timerange, list()).append(formula)
    return mapping
    
    
def create_synthetic_records(base_record, data, formulas):
    rtype, timerange = base_record
    
    # Filter all formulas involving base record.
    record_formulas = formulas.get(rtype, dict()).get(timerange, None)
    if not record_formulas:
        return list()
    
    # Filter calculable formulas which output is not present in data
    calc_formulas = [ 
        formula for formula in record_formulas 
        if formula.is_calculable(data) and not formula.is_calculated(data)
    ]

    # Create synthetic records
    synthetic_records = [ 
        {
            "value": formula.calculate(data) ,
            "rtype": formula.lhs.rtype,
            "timerange": formula.lhs.timerange
        }
        for formula in calc_formulas 
    ]

    # Update data
    for record in synthetic_records:
        data.setdefault(record["rtype"], dict())[record["timerange"]] =\
            record["value"]
        
    # Create synthetic records for newly created records
    synthetic_records_2nd = concatenate_lists(
        create_synthetic_records(
            (record["rtype"], record["timerange"]), data, formulas
        )
        for record in synthetic_records
    )

    synthetic_records.extend(synthetic_records_2nd)
    return synthetic_records


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