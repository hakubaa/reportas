from collections import UserDict

from rparser.synthetic import (
    Formula, FormulaComponent, Record, TimeframeSpec, Timeframe,
    RecordsDataset
)


class DictRecordsDataset(RecordsDataset, UserDict):

    def _get_record(self, item):
        try:
            return self[item]
        except KeyError:
            raise DatasetNotFoundError()

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
    def create_from_records(cls, records):
        dataset = cls()
        dataset.insert(records)
        return dataset            


def convert_db_formula(db_formula):
    formula = Formula(spec=db_formula.rtype)
    for item in db_formula.rhs:
        formula.add_component(FormulaComponent(
            spec=item.rtype, sign=item.sign
        ))
    return formula


def convert_db_formulas(db_formulas):
    return [ convert_db_formula(formula) for formula in db_formulas ]


def convert_db_record(db_record, fiscal_year=None):
    timeframe = Timeframe(*db_record.project_onto_fiscal_year(fiscal_year))
    spec = TimeframeSpec(spec=db_record.rtype, timeframe=timeframe)
    record = Record(
        spec=spec, value=db_record.value, synthetic=db_record.synthetic
    )
    return record


def convert_db_records(records):
    return [ convert_db_record(record) for record in records ]