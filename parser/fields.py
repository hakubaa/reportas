from collections import namedtuple


class FieldType(Enum):
    '''Represent type of field in terms of time.'''
    POINT_IN_TIME = 1
    PIT = 1 # shortcut for POINT_IN_TIME
    PERIOD_OF_TIME = 2
    POT = 2 # shortcut for PERIOD_OF_TIME


class FieldTimeRange(Enum):
    '''Represent type of field's time range.'''
    POINT = 0 # no time range (fake field for point-in-time fields)
    P = 0 # shortcut for POINT
    YEAR = 1
    Y = 1 # shortcut for YEAR
    QUARTER = 2
    Q = 2 # shortcut for QUARTER
    HALF_YEAR = 3
    H = 3 # shortcut for HALF_YEAR


Field = namedtuple("Field", "type", "time_range", "period")


class Field:

    def create_field_record


def register_field(cls):
    '''Class decorator.'''
    pass


def identify_field(label):
    '''Find the most appripriate field type for given label.'''
    pass