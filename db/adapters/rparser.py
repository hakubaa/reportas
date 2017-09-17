from collections import UserDict, namedtuple
from datetime import date, timedelta
import itertools

from rparser import synthetic
from db import utils
from db import models

################################################################################
# TRANSFORM DB ENTITITES INTO RPARSER ENTITITES
################################################################################

class DictRecordsDataset(synthetic.RecordsDataset, UserDict):

    def _get_record(self, item):
        try:
            return self[item]
        except KeyError:
            raise synthetic.DatasetNotFoundError()

    def get_value(self, item):
        return self._get_record(item)["value"]

    def exists(self, item):
        return item in self

    def is_synthetic(self, item):
        return self._get_record(item)["synthetic"]

    def insert(self, items, synthetic = None):
        for item in items:
            self.data[item.spec] = {
                "value": item.value, 
                "synthetic": getattr(item, "synthetic", synthetic) 
            }

    @classmethod
    def create_from_db_records(cls, db_records):
        return cls.create_from_records(convert_db_records(db_records))

    @classmethod
    def create_from_records(cls, records):
        dataset = cls()
        dataset.insert(records)
        return dataset


def convert_db_formula(db_formula):
    formula = synthetic.Formula(spec=db_formula.rtype)
    for item in db_formula.rhs:
        formula.add_component(synthetic.FormulaComponent(
            spec=item.rtype, sign=item.sign
        ))
    return formula


def convert_db_formulas(db_formulas):
    return [ convert_db_formula(formula) for formula in db_formulas ]


def convert_db_record(db_record, fiscal_year=None):
    timeframe = synthetic.Timeframe(*db_record.project_onto_fiscal_year(fiscal_year))
    spec = synthetic.TimeframeSpec(spec=db_record.rtype, timeframe=timeframe)
    record = synthetic.Record(
        spec=spec, value=db_record.value, synthetic=db_record.synthetic
    )
    return record


def convert_db_records(records):
    return [ convert_db_record(record) for record in records ]
    
################################################################################

################################################################################
# TRANSFORM RPARSER ENTITITES INTO DB ENTITITES
################################################################################

def convert_rparser_record(session, record, company, fiscal_year):
    rtype = record.spec.spec
    timeframe = record.spec.timeframe
    
    record = models.Record.update_or_create(
        session,
        defaults = { "value": record.value, "synthetic": True },
        company = company, rtype = rtype,
        timerange = (
            0 if rtype.timeframe == models.FinancialStatement.PIT 
            else timeframe.end - timeframe.start + 1
        ),
        timestamp = project_timeframe_onto_fiscal_year(
            timeframe, fiscal_year
        ).end
    )
    return record
    
    
def project_timeframe_onto_fiscal_year(timeframe, fiscal_year):
    start_month = fiscal_year.start.month + timeframe.start - 1
    if start_month > 12:
        start_month -= 12
        start_year = fiscal_year.start.year + 1
    else:
        start_year = fiscal_year.start.year
    start_timestamp = date(start_year, start_month, 1)
    
    end_month = fiscal_year.start.month + timeframe.end - 1
    if end_month > 12:
        end_month -= 12
        end_year = fiscal_year.start.year + 1
    else:
        end_year = fiscal_year.start.year

    if end_month == 12:
        end_timestamp = date(end_year+1, 1, 1) - timedelta(days=1)    
    else:
        end_timestamp = date(end_year, end_month+1, 1) - timedelta(days=1)
    
    return synthetic.Timeframe(start=start_timestamp, end=end_timestamp)
    
################################################################################

################################################################################
# CREATE SYNTHETIC RECORDS
################################################################################

def create_synthetic_records(base_records, db_records, db_formulas):
    dataset = DictRecordsDataset.create_from_db_records(db_records)
    records_spec = set(
        record.rtype for record in itertools.chain(base_records, db_records)
                     if record.rtype.timeframe == models.FinancialStatement.POT
    )

    formulas = convert_db_formulas(db_formulas)
    formulas = {
        models.FinancialStatement.POT: synthetic.create_inverted_mapping(
            synthetic.create_pot_formulas(formulas, records_spec)
        ),
        models.FinancialStatement.PIT: synthetic.create_inverted_mapping(
            synthetic.create_pit_formulas(formulas)
        )
    }
    
    synthetic_records = utils.concatenate_lists(
        synthetic.create_synthetic_records(
            spec=convert_db_record(record).spec, dataset=dataset, 
            formulas=formulas[record.rtype.timeframe]
        ) 
        for record in base_records
    )
    
    return synthetic_records
    
################################################################################