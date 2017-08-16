import unittest
from unittest import mock
from collections import UserDict

from rparser.synthetic import (
    RecordsDataset, FormulaComponent, Timeframe, TimeframeSpec,
    DatasetNotFoundError, Formula, create_inverted_mapping,
    extend_formula_with_timeframe,  remove_duplicate_formulas,
    create_synthetic_records, Record
)


class DictRecordsDataset(RecordsDataset, UserDict):
    
    def get_value(self, item):
        try:
            return self[item]
        except KeyError:
            raise DatasetNotFoundError()

    def exists(self, item):
        return item in self
            
    def is_synthetic(self, item):
        return False

    def insert(self, items, synthetic = None):
        pass


class ExtDictRecordsDataset(RecordsDataset, UserDict):

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

            
class FormulaComponentTest(unittest.TestCase):

    def test_get_value_returns_correct_value(self):
        dataset = DictRecordsDataset({"TOTAL_ASSETS": 100, "FIXED_ASSETS": 50})
        component = FormulaComponent(spec="TOTAL_ASSETS", sign=1)
        
        value = component.get_value(dataset)
        
        self.assertEqual(value, 100)
        
    def test_get_value_raises_database_not_found_error(self):
        dataset = DictRecordsDataset({"FIXED_ASSETS": 50})
        component = FormulaComponent(spec="TOTAL_ASSETS", sign=1)
        
        with self.assertRaises(DatasetNotFoundError):
            component.get_value(dataset)
            
    def test_calculate_returns_correct_value(self):
        dataset = DictRecordsDataset({"TOTAL_ASSETS": 100, "FIXED_ASSETS": 50})
        component = FormulaComponent(spec="TOTAL_ASSETS", sign=-1)
        
        value = component.calculate(dataset)
        
        self.assertEqual(value, -100)
        
    def test_is_calculable_returns_true_when_data_is_available(self):
        dataset = DictRecordsDataset({"TOTAL_ASSETS": 100, "FIXED_ASSETS": 50})
        component = FormulaComponent(spec="TOTAL_ASSETS", sign=-1)  
        
        self.assertTrue(component.is_calculable(dataset))
        
    def test_is_calculable_returns_false_when_data_is_not_available(self):
        dataset = DictRecordsDataset({"FIXED_ASSETS": 50})
        component = FormulaComponent(spec="TOTAL_ASSETS", sign=1)
        
        self.assertFalse(component.is_calculable(dataset))
        
    def test_components_with_the_same_spec_and_sign_are_the_same(self):
        component1 = FormulaComponent(spec="ASSETS", sign=1)
        component2 = FormulaComponent(spec="ASSETS", sign=1)
        
        self.assertEqual(component1, component2)
        self.assertEqual(hash(component1), hash(component2))
        

class FormulaTest(unittest.TestCase):
    
    def test_calculate_delagates_calculation_to_components(self):
        dataset = mock.Mock()
        c1 = mock.Mock()
        c1.calculate.return_value = 10
        c2 = mock.Mock()
        c2.calculate.return_value = 90
        
        formula = Formula(spec="TEST", components = [c1, c2])
        
        value = formula.calculate(dataset)
        
        self.assertEqual(value, 100)
        self.assertTrue(c1.calculate.called)
        self.assertTrue(c2.calculate.called)
        
    def test_is_calculable_tests_calculable_of_formula_components(self):
        dataset = mock.Mock()
        c1 = mock.Mock()
        c1.is_calculable.return_value = True
        c2 = mock.Mock()
        c2.is_calculable.return_value = True
        formula = Formula(spec="TEST", components = [c1, c2])
        
        value = formula.is_calculable(dataset)
        
        self.assertTrue(c1.is_calculable.called)
        self.assertTrue(c2.is_calculable.called)
        self.assertTrue(value)
        
    def test_formula_with_the_same_components_and_spec_are_equal(self):
        f1 = Formula(spec="TEST", components = [FormulaComponent("TEST", 1)])
        f2 = Formula(spec="TEST", components = [FormulaComponent("TEST", 1)])
        
        self.assertEqual(f1, f2)
        self.assertEqual(hash(f1), hash(f2))
        
    def test_transform_formula(self):
        formula = Formula(
            spec="TOTAL_ASSETS", components = [
                FormulaComponent("FIXED_ASSETS", 1),
                FormulaComponent("CURRENT_ASSETS", 1)
            ]
        )
        
        fa_formula = formula.transform("FIXED_ASSETS")
        
        self.assertEqual(fa_formula.spec, "FIXED_ASSETS")
        
        c1 = next(filter(lambda x: x.spec == "TOTAL_ASSETS", fa_formula))
        self.assertEqual(c1.sign, 1)
        
        c2 = next(filter(lambda x: x.spec == "CURRENT_ASSETS", fa_formula))
        self.assertEqual(c2.sign, -1)
        
    def test_transform_raises_keyerror_when_spec_not_part_of_formula(self):
        formula = Formula(
            spec="TOTAL_ASSETS", components = [
                FormulaComponent("FIXED_ASSETS", 1),
                FormulaComponent("CURRENT_ASSETS", 1)
            ]
        )
        
        with self.assertRaises(KeyError):
            formula.transform("FAKE_SPEC")
            
    def test_create_timeframe_formula(self):
        formula = Formula.create_timeframe_formula(
            spec="TOTAL_ASSETS",
            timeframe_spec=(
                Timeframe(1, 6), 
                [(Timeframe(1, 3), 1), (Timeframe(4, 6), -1)]
            )
        )

        self.assertIsInstance(formula.spec, TimeframeSpec)
        self.assertEqual(formula.spec.timeframe, Timeframe(1, 6))
        self.assertEqual(formula.spec.spec, "TOTAL_ASSETS")
        
        self.assertEqual(len(formula.rhs), 2)
        self.assertIsInstance(formula.rhs[0].spec, TimeframeSpec)
        
        
class TestUtils(unittest.TestCase):
    
    def create_formula(self, spec, rhs):
        formula = Formula(spec=spec)
        for spec, sign in rhs:
            formula.add_component(FormulaComponent(
                spec=spec, sign=sign
            ))
        return formula

    def create_default_formula(self):
        return self.create_formula(
            "TOTAL_ASSETS",
            [("FIXED_ASSETS",1), ("CURRENT_ASSETS",1)]
        )
        
    def test_create_inverted_mapping(self):
        formula = self.create_default_formula()
        
        formulas = create_inverted_mapping([formula])
        
        self.assertEqual(len(formulas), 2)
        self.assertIn("FIXED_ASSETS", formulas)
        self.assertIn("CURRENT_ASSETS", formulas)
        self.assertCountEqual(formulas["FIXED_ASSETS"], [formula])
        self.assertCountEqual(formulas["CURRENT_ASSETS"], [formula])
    
    def test_extend_formula_with_timeframe(self):
        ext_formula = extend_formula_with_timeframe(
            self.create_default_formula(), Timeframe(start=1, end=12)
        )
        
        self.assertIsInstance(ext_formula.spec, TimeframeSpec)
        self.assertEqual(ext_formula.spec.timeframe, Timeframe(start=1, end=12))
        
        self.assertIsInstance(ext_formula.rhs[0].spec, TimeframeSpec)
        self.assertEqual(
            ext_formula.rhs[0].spec.timeframe, Timeframe(start=1, end=12)
        )
        
        self.assertIsInstance(ext_formula.rhs[1].spec, TimeframeSpec)
        self.assertEqual(
            ext_formula.rhs[1].spec.timeframe, Timeframe(start=1, end=12)
        )
        
    def test_remove_duplicate_formulas(self):
        f1 = Formula(spec="TEST", components = [FormulaComponent("TEST", 1)])
        f2 = Formula(spec="TEST", components = [FormulaComponent("TEST", 1)]) 
        
        formulas = remove_duplicate_formulas([f1, f2])
        
        self.assertEqual(len(formulas), 1)

    def test_create_synthetic_records(self):
        formula = self.create_default_formula()
        
        dataset = ExtDictRecordsDataset({
            "FIXED_ASSETS": {"value": 60, "synthetic": False},
            "CURRENT_ASSETS": {"value": 40, "synthetic": False}
        })
        
        formulas = create_inverted_mapping([formula])
        records = create_synthetic_records("CURRENT_ASSETS", dataset, formulas)
        
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].spec, "TOTAL_ASSETS")
        self.assertEqual(records[0].value, 100)

    def test_create_synthetic_records_create_related_records(self):
        formula_ta = self.create_default_formula()
        formula_li = self.create_formula(
            "TOTAL_LIABILITIES", [("TOTAL_ASSETS", 1)]
        )
        formulas = create_inverted_mapping([formula_ta, formula_li])

        dataset = ExtDictRecordsDataset({
            "FIXED_ASSETS": {"value": 60, "synthetic": False},
            "CURRENT_ASSETS": {"value": 40, "synthetic": False}
        })

        records = create_synthetic_records("CURRENT_ASSETS", dataset, formulas)

        self.assertEqual(len(records), 2)

        record = next(filter(lambda item: item.spec == "TOTAL_LIABILITIES", records))
        self.assertEqual(record.value, 100)

    def test_create_synthetic_records_does_not_recalculate_genuine_records(self):
        formula_ta = self.create_default_formula()
        formulas = create_inverted_mapping([formula_ta])

        dataset = ExtDictRecordsDataset({
            "FIXED_ASSETS": {"value": 60, "synthetic": False},
            "CURRENT_ASSETS": {"value": 40, "synthetic": False},
            "TOTAL_ASSETS": {"value": 100, "synthetic": False}
        })

        records = create_synthetic_records("CURRENT_ASSET", dataset, formulas)

        self.assertEqual(len(records), 0)

    def test_create_synthetic_records_with_timeframe_formulas(self):
        formula = Formula.create_timeframe_formula(
            spec="TOTAL_ASSETS",
            timeframe_spec=(
                Timeframe(1, 6), 
                [(Timeframe(1, 3), 1), (Timeframe(4, 6), 1)]
            )
        )
        formulas = create_inverted_mapping([formula])
        dataset = ExtDictRecordsDataset({
            TimeframeSpec("TOTAL_ASSETS", Timeframe(1, 3)): { 
                "value": 50, "synthetic": False
            },
            TimeframeSpec("TOTAL_ASSETS", Timeframe(4, 6)): {
                "value": 60, "synthetic": False
            }
        })

        records = create_synthetic_records(
            TimeframeSpec("TOTAL_ASSETS", Timeframe(4, 6)), dataset, formulas
        )

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].spec.spec, "TOTAL_ASSETS")
        self.assertEqual(records[0].spec.timeframe, Timeframe(1, 6))
        self.assertEqual(records[0].value, 110)
        
    def test_csr_updates_data(self):
        formula = self.create_default_formula()
        
        dataset = ExtDictRecordsDataset({
            "FIXED_ASSETS": {"value": 60, "synthetic": False},
            "CURRENT_ASSETS": {"value": 40, "synthetic": False}
        })
        
        formulas = create_inverted_mapping([formula])
        records = create_synthetic_records("CURRENT_ASSETS", dataset, formulas)    

        self.assertTrue(dataset.exists("TOTAL_ASSETS"))
        self.assertEqual(dataset.get_value("TOTAL_ASSETS"), 100)

    def test_csr_updates_synthetic_records(self):
        formula = self.create_default_formula()
        
        dataset = ExtDictRecordsDataset({
            "FIXED_ASSETS": {"value": 60, "synthetic": False},
            "CURRENT_ASSETS": {"value": 40, "synthetic": False},
            "TOTAL_ASSETS": {"value": 200, "synthetic": True}
        })
        
        formulas = create_inverted_mapping([formula])
        records = create_synthetic_records("CURRENT_ASSETS", dataset, formulas)  

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].spec, "TOTAL_ASSETS")
        self.assertEqual(records[0].value, 100)

    def test_csr_does_not_update_genuine_records(self):
        formula = self.create_default_formula()
        
        dataset = ExtDictRecordsDataset({
            "FIXED_ASSETS": {"value": 60, "synthetic": False},
            "CURRENT_ASSETS": {"value": 40, "synthetic": False},
            "TOTAL_ASSETS": {"value": 200, "synthetic": False}
        })
        
        formulas = create_inverted_mapping([formula])
        records = create_synthetic_records("CURRENT_ASSETS", dataset, formulas)  
          
        self.assertEqual(len(records), 0)

    def test_csr_creates_synthetic_records_from_synthetic_records(self):
        formula = self.create_default_formula()
        
        dataset = ExtDictRecordsDataset({
            "FIXED_ASSETS": {"value": 60, "synthetic": True},
            "CURRENT_ASSETS": {"value": 40, "synthetic": True},
            "TOTAL_ASSETS": {"value": 200, "synthetic": True}
        })
        
        formulas = create_inverted_mapping([formula])
        records = create_synthetic_records("CURRENT_ASSETS", dataset, formulas)  

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].spec, "TOTAL_ASSETS")
        self.assertEqual(records[0].value, 100)