from datetime import datetime
import json

from flask import url_for

from app import db
from app.rapi import api
from db.serializers import DatetimeEncoder
from db.models import (
    Company, Report, CompanyRepr, RecordType, RecordTypeRepr, Record,
    RecordFormula, FormulaComponent, FinancialStatement
)
from app.models import Permission, Role, User, DBRequest

from tests.app import AppTestCase, create_and_login_user


def create_test_formulas():
    ftype = FinancialStatement.get_or_create(
        db.session, name="bls", timeframe=FinancialStatement.POT
    )
    total_assets = RecordType(name="TOTAL_ASSETS", ftype=ftype)
    current_assets = RecordType(name="CURRENT_ASSETS", ftype=ftype)
    fixed_assets = RecordType(name="FIXED_ASSETS", ftype=ftype)
    db.session.add_all((total_assets, current_assets, fixed_assets))
    db.session.flush()    
    
    formula1 = RecordFormula(rtype=total_assets)
    formula1.add_component(rtype=current_assets, sign=1)
    formula1.add_component(rtype=fixed_assets, sign=1)
    db.session.add(formula1)
    
    formula2 = RecordFormula(rtype=current_assets)
    formula2.add_component(rtype=total_assets, sign=1)
    formula2.add_component(rtype=fixed_assets, sign=-1)
    db.session.add(formula2)
    
    formula3 = RecordFormula(rtype=fixed_assets)
    formula3.add_component(rtype=total_assets, sign=1)
    formula3.add_component(rtype=fixed_assets, sign=-1)
    db.session.add(formula3)
    
    db.session.commit()
    
    return {
        "total_assets": formula1,
        "current_asssets": formula2,
        "fixed_assets": formula3
    }


class FormulaListViewTest(AppTestCase):
    
    @create_and_login_user()
    def test_response_for_get_request_contains_list_of_formulas(self):
        create_test_formulas()
        
        rtype = db.session.query(RecordType).\
                    filter_by(name="TOTAL_ASSETS").one()
        response = self.client.get(
            url_for("rapi.rtype_formula_list", rid=rtype.id)
        )
        
        data = response.json
        self.assertEqual(data["count"], 1)

        formula = data["results"][0]
        self.assertEqual(len(formula["components"]), 2)
        
        names = [
            component["rtype"] for component in formula["components"]
        ]
        self.assertCountEqual(names, ["CURRENT_ASSETS", "FIXED_ASSETS"])
        
    
    @create_and_login_user(pass_user=True)
    def test_post_request_creates_dbrequest(self, user):
        create_test_formulas()
        
        rtype = db.session.query(RecordType).\
                    filter_by(name="TOTAL_ASSETS").one()
                    
        response = self.client.post(
            url_for("rapi.rtype_formula_list", rid=rtype.id),
            data=json.dumps({}), content_type="application/json"
        )
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "create")
        self.assertEqual(dbrequest.model, "RecordFormula")   
        
    @create_and_login_user(pass_user=True)
    def test_rtype_id_set_by_default_in_dbrequest(self, user):
        create_test_formulas()
        
        rtype = db.session.query(RecordType).\
                    filter_by(name="TOTAL_ASSETS").one()
                    
        response = self.client.post(
            url_for("rapi.rtype_formula_list", rid=rtype.id),
            data=json.dumps({"rtype_id": 11}), 
            content_type="application/json"
        )
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        data = json.loads(dbrequest.data)
        self.assertEqual(data["rtype_id"], rtype.id)
        
        
class FormulaDetailViewTest(AppTestCase):

    @create_and_login_user()
    def test_get_request_returns_detail_of_repr(self):
        create_test_formulas()
        rtype = db.session.query(RecordType).\
                    filter_by(name="TOTAL_ASSETS").one()
        formula = rtype.formulas[0]
        response = self.client.get(
            url_for("rapi.rtype_formula_detail", rid=rtype.id, fid=formula.id)
        )
        data = response.json
        self.assertIn("components", data)

    @create_and_login_user(pass_user=True)
    def test_delete_request_creates_dbrequest(self, user):
        create_test_formulas()
        rtype = db.session.query(RecordType).\
                    filter_by(name="TOTAL_ASSETS").one()
        formula = rtype.formulas[0]
        response = self.client.delete(
            url_for("rapi.rtype_formula_detail", rid=rtype.id, fid=formula.id)
        )
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        self.assertEqual(dbrequest.model, "RecordFormula")
        self.assertEqual(dbrequest.action, "delete")
        self.assertEqual(dbrequest.user, user)
        
    
class FormulaComponentListViewTest(AppTestCase):
    
    @create_and_login_user
    def test_response_for_get_request_contains_list_of_formulas(self):
        create_test_formulas()
        rtype = db.session.query(RecordType).\
                    filter_by(name="TOTAL_ASSETS").one()
        formula = rtype.formulas[0]
                    
        response = self.client.get(
            url_for("rapi.formula_component_list", rid=rtype.id, fid=formula.id)
        )
    
        data = response.json["results"]
        self.assertEqual(len(data), 2)
        
        names = [ data["rtype"]["name"] for component in data ]
        self.assertCountEqual(names, ["CURRENT_ASSES", "FIXED_ASSSETS"])
        
    @create_and_login_user
    def test_404_when_invalid_rtype_id(self):
        create_test_formulas()
        rtype = db.session.query(RecordType).\
                    filter_by(name="TOTAL_ASSETS").one()
        formula = rtype.formulas[0]    
        
        response = self.client.get(
            url_for("rapi.formula_component_list", rid=rtype.id+1, fid=formula.id)
        )  
        self.assertEqual(response.status_code, 404)
        
    @create_and_login_user
    def test_404_when_invalid_formula_id(self):
        create_test_formulas()
        rtype = db.session.query(RecordType).\
                    filter_by(name="TOTAL_ASSETS").one()
        formula = rtype.formulas[0]    
        
        response = self.client.get(
            url_for("rapi.formula_component_list", rid=rtype.id, fid=formula.id+1)
        )  
        self.assertEqual(response.status_code, 404)   
        
    @create_and_login_user(pass_user=True)
    def test_post_request_creates_dbrequest(self, user):
        create_test_formulas()
        ftype = db.session.query(FinancialStatement).one()
        new_rtype = RecordType(name="TEST TYPE", ftype=ftype)
        db.session.add(new_rtype)
        db.session.commit()
        
        rtype = db.session.query(RecordType).\
                    filter_by(name="TOTAL_ASSETS").one()
        formula = rtype.formulas[0]
                    
        response = self.client.post(
            url_for("rapi.formula_component_list", rid=rtype.id, fid=formula.id),
            data=json.dumps({"sign": 1, "rtype_id": new_rtype.id}), 
            content_type="application/json"
        )
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(dbrequest.action, "create")
        self.assertEqual(dbrequest.model, "FormulaComponent")
        
        data = json.loads(dbrequest.data)
        self.assertEqual(data["sign"], 1)
        self.assertEqual(data["rtype_id"], new_rtype.id)
        self.assertEqual(data["formula_id"], formula.id)
        
    
class FormulaComponentDetailViewTest(AppTestCase):
    
    @create_and_login_user()
    def test_get_request_returns_detail_of_component(self):
        create_test_formulas()
        rtype = db.session.query(RecordType).\
                    filter_by(name="TOTAL_ASSETS").one()
        formula = rtype.formulas[0]
        component = formula.components[0]
        
        response = self.client.get(
            url_for("rapi.formula_component_detail", rid=rtype.id, 
                    fid=formula.id, cid=component.id)
        )
        data = response.json
        self.assertEqual(data["rtype"], component.rtype.name)
        self.assertEqual(data["sign"], 1)

    @create_and_login_user(pass_user=True)
    def test_put_request_creates_dbrequet(self, user):
        create_test_formulas()
        rtype = db.session.query(RecordType).\
                    filter_by(name="TOTAL_ASSETS").one()
        formula = rtype.formulas[0]
        component = formula.components[0] 
        
        response = self.client.put(
            url_for("rapi.formula_component_detail", rid=rtype.id, 
                    fid=formula.id, cid=component.id),
            data=json.dumps({"sign": -1}, cls=DatetimeEncoder),
            content_type="application/json"
        )
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)

        data = json.loads(dbrequest.data)
        self.assertEqual(dbrequest.action, "update")
        self.assertEqual(dbrequest.user, user)
        self.assertEqual(data["id"], component.id)
        self.assertEqual(data["formula_id"], formula.id)

    @create_and_login_user(pass_user=True)
    def test_delete_request_deletes_repr(self, user):
        create_test_formulas()
        rtype = db.session.query(RecordType).\
                    filter_by(name="TOTAL_ASSETS").one()
        formula = rtype.formulas[0]
        component = formula.components[0] 
        
        response = self.client.delete(
            url_for("rapi.formula_component_detail", rid=rtype.id, 
                    fid=formula.id, cid=component.id),
        )
        
        dbrequest = db.session.query(DBRequest).first()
        self.assertIsNotNone(dbrequest)
        self.assertEqual(dbrequest.action, "delete")
        self.assertEqual(dbrequest.user, user)
        
        data = json.loads(dbrequest.data)
        self.assertEqual(data["id"], component.id)
        self.assertEqual(data["formula_id"], component.formula_id)