from collections import namedtuple
import collections
from functools import reduce
import operator
from datetime import date, timedelta
import abc

from rparser.utils import concatenate_lists


Timeframe = namedtuple("Timeframe", field_names="start, end")
TimeframeSpec = namedtuple("TimeframeSpec", field_names="spec, timeframe")
Record = namedtuple("Record", field_names="spec, value, synthetic")


class RecordsDataset(abc.ABC):
    
    @abc.abstractmethod
    def get_value(self, item):
        '''Return value from database for the item.'''
        
    @abc.abstractmethod
    def exists(self, item):
        '''Check whether the item exists in dataset.'''

    @abc.abstractmethod
    def insert(self, items, synthetic=None):
        '''Update items in dataset.'''

    @abc.abstractmethod
    def is_synthetic(self, item):
        '''Check whether the item is synthetic.'''
        
    def is_genuine(self, item):
        '''Check whether the item is genuine.'''
        return not self.is_synthetic(item)


class DatasetNotFoundError(Exception):
    pass


class FormulaComponent:

    def __init__(self, spec, sign):
        self.spec = spec
        self.sign = sign

    def __repr__(self):
        cls_name = self.__class__.__name__
        return "{}({!r}, {})".format(cls_name, self.spec, self.sign)

    def __hash__(self):
        return hash(self.spec) ^ hash(self.sign)

    def __eq__(self, other):
        if self.spec != other.spec or self.sign != other.sign:
            return False
        return True
        
    def get_value(self, dataset):
        return dataset.get_value(self.spec)
    
    def calculate(self, dataset):
        return self.sign * self.get_value(dataset)
    
    def is_calculable(self, dataset):
        return dataset.exists(self.spec)
            
            
class Formula:

    def __init__(self, spec, components=None):
        self.spec = spec
        self.components = components or list()
    
    @property
    def lhs(self):
        return self.spec
        
    @property
    def rhs(self):
        return self.components
        
    def __hash__(self):
        return hash(self.spec) ^ reduce(operator.xor, map(hash, self.components))   

    def __eq__(self, other):
        if self.spec != other.spec:
            return False
        if len(self.components) != len(other.components):
            return False
        for c1, c2 in zip(self.components, other.components):
            if c1 != c2:
                return False
        return True

    def __iter__(self):
        return iter(self.components)

    def __len__(self):
        return len(self.components)

    def __repr__(self):
        msg = "Formula: {!r} = " + " + ".join("{!r}" for _ in range(len(self)))
        return msg.format(self.spec, *self.components)

    def add_component(self, component):
        self.components.append(component)
    
    def calculate(self, data):
        return sum(item.calculate(data) for item in self)
    
    def is_calculable(self, data):
        return all(map(lambda item: item.is_calculable(data), self))
        
    def transform(self, spec):
        try:
            new_lhs = next(filter(lambda item: item.spec == spec, self))
        except StopIteration:
            raise KeyError("component with spec does not exist")
            
        new_formula = Formula(spec=new_lhs.spec)
        sign_adjustment = new_lhs.sign * (-1) # -1 for moving to other site
        new_formula.add_component(FormulaComponent(
            spec=self.spec, sign=new_lhs.sign
        ))
        for component in self:
            if component.spec != spec:
                new_formula.add_component(FormulaComponent(
                    spec=component.spec, sign=component.sign*sign_adjustment
                ))
        return new_formula
        
    def extend_with_timeframe(self, timeframe):
        new_formula = Formula(spec=TimeframeSpec(self.spec, timeframe))
        for item in self:
            new_formula.add_component(
                FormulaComponent(
                    spec=TimeframeSpec(item.spec, timeframe), sign=item.sign
                )
            )
        return new_formula
        
    @classmethod
    def create_timeframe_formula(cls, spec, timeframe_spec):
        formula = cls(spec=TimeframeSpec(spec=spec, timeframe=timeframe_spec[0]))
        for timeframe, sign in timeframe_spec[1]:
            formula.add_component(FormulaComponent(
                spec=TimeframeSpec(spec=spec, timeframe=timeframe), sign=sign
            ))
        return formula
        

def extend_formula_with_timeframe(formula, timeframe):
    new_formula = Formula(spec=TimeframeSpec(formula.spec, timeframe))
    for item in formula:
        new_formula.add_component(
            FormulaComponent(
                spec=TimeframeSpec(item.spec, timeframe), sign=item.sign
            )
        )
    return new_formula
    

def create_inverted_mapping(formulas):
    mapping = dict()
    for formula in formulas:
        for item in formula:
            mapping.setdefault(item.spec, list()).append(formula)
    return mapping
    
    
def create_synthetic_records(spec, dataset, formulas, exclude=None):
    exclude = set() if exclude is None else set(exclude)
    if spec in exclude: return list()

    # Filter all formulas involving the spec.
    record_formulas = formulas.get(spec, None)
    if not record_formulas: return list()

    # Filter calculable formulas which output is not present in data
    calculable_formulas = [ 
        formula for formula in record_formulas 
        if formula.is_calculable(dataset) \
           and (not dataset.exists(formula.spec) 
                or dataset.is_synthetic(formula.spec)) \
           and not formula.spec in exclude
    ]

    if len(calculable_formulas) == 0: return list()

    # Create synthetic records
    synthetic_records = [
        Record(spec=formula.spec, value=formula.calculate(dataset))
        for formula in calculable_formulas 
    ]

    exclude.update( # exclude formulas' components for potential recalculation
        item.spec for formula in calculable_formulas for item in formula.rhs
    )
    exclude.add(spec)
    dataset.insert(synthetic_records, synthetic=False)

    # Create synthetic records for newly created records
    synthetic_records_2nd = concatenate_lists(
        create_synthetic_records(record.spec, dataset, formulas, exclude)
        for record in synthetic_records
    )

    synthetic_records.extend(synthetic_records_2nd)
    return synthetic_records
    
    
def remove_duplicate_formulas(formulas):
    return list(set(formulas))   
    
    
def extend_formulas_with_timeframes(formulas, timeframes):
    if not isinstance(formulas, collections.Iterable):
        formulas = [formulas]

    return [ 
        formula.extend_with_timeframe(timeframe) 
        for formula in formulas
        for timeframe in timeframes 
    ]
    
################################################################################    


# def create_formulas_for_csr(
#     base_formulas, timeranges=None, timerange_formulas=None, rtypes=None
# ):
#     if not isinstance(base_formulas, collections.Iterable):
#         base_formulas = [base_formulas]
#     formulas = list(base_formulas)
#     formulas.extend(create_db_formulas_transformations(formulas))
#     formulas = convert_db_formulas(formulas)
#     formulas = extend_formulas_with_timerange(formulas, timeranges)
#     if timerange_formulas and rtypes:
#         formulas.extend(create_timerange_formulas(rtypes, timerange_formulas))
#     formulas = remove_duplicated_formulas(formulas)
#     return formulas

# def project_timerange_onto_fiscal_year(timerange, fiscal_year):
#     start_month = fiscal_year.start.month + timerange.start - 1
#     if start_month > 12:
#         start_month -= 12
#         start_year = fiscal_year.start.year + 1
#     else:
#         start_year = fiscal_year.start.year
#     start_timestamp = date(start_year, start_month, 1)
    
#     end_month = fiscal_year.start.month + timerange.end - 1
#     if end_month > 12:
#         end_month -= 12
#         end_year = fiscal_year.start.year + 1
#     else:
#         end_year = fiscal_year.start.year

#     if end_month == 12:
#         end_timestamp = date(end_year+1, 1, 1) - timedelta(days=1)    
#     else:
#         end_timestamp = date(end_year, end_month+1, 1) - timedelta(days=1)
    
#     return TimeRange(start=start_timestamp, end=end_timestamp)
