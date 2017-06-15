from flask import url_for

from app import db
from app.rapi import api
from app.rapi.views import (
    CompanyListAPI, CompanyReprListAPI, RecordTypeListAPI
)
from db.models import (
    Company, Report, CompanyRepr, RecordType, RecordTypeRepr
)

from tests.app import AppTestCase


class TestCompanyListAPI(AppTestCase):

    def test_get_request_returns_json_response(self):
        response = self.client.get(api.url_for(CompanyListAPI))
        self.assertEqual(response.content_type, "application/json")

    def test_get_request_returns_list_of_companies(self):
        comp1 = Company.create(db.session, name="TEST1", isin="#TEST1")
        comp2 = Company.create(db.session, name="TEST2", isin="#TEST2")
        db.session.commit()
        response = self.client.get(api.url_for(CompanyListAPI))
        data = response.json["results"]
        self.assertEqual(len(data), 2)

    def test_get_request_returns_companies_data(self):
        comp = Company.create(db.session, name="TEST", isin="123#TEST")
        db.session.commit()
        response = self.client.get(api.url_for(CompanyListAPI))
        data = response.json["results"][0]
        self.assertEqual(data["name"], comp.name)
        self.assertEqual(data["isin"], comp.isin)

    def test_get_request_returns_hyperlinks_to_detail_view(self):
        comp = Company.create(db.session, name="TEST", isin="123#TEST")
        CompanyRepr.create(db.session, value="TEST Repr", company=comp)
        db.session.commit()
        response = self.client.get(url_for("rapi.company_list"))
        data = response.json["results"][0]
        self.assertIsNotNone(data["uri"])
        self.assertEqual(data["uri"], url_for("rapi.company", id=comp.id))

    def test_order_results_with_sort_parameter(self):
        Company.create(db.session, name="BB", isin="BB")
        Company.create(db.session, name="AA", isin="AA")
        Company.create(db.session, name="CC", isin="CC")
        db.session.commit()
        response = self.client.get(
            url_for("rapi.company_list"),
            query_string={"sort": "name"}
        )
        data = response.json["results"]
        self.assertEqual(data[0]["name"], "AA")
        self.assertEqual(data[1]["name"], "BB")
        self.assertEqual(data[2]["name"], "CC")

    def test_sort_in_reverse_order(self):
        Company.create(db.session, name="BB", isin="BB")
        Company.create(db.session, name="AA", isin="AA")
        Company.create(db.session, name="CC", isin="CC")
        db.session.commit()
        response = self.client.get(
            url_for("rapi.company_list"),
            query_string={"sort": "-name"}
        )
        data = response.json["results"]
        self.assertEqual(data[0]["name"], "CC")
        self.assertEqual(data[1]["name"], "BB")
        self.assertEqual(data[2]["name"], "AA")

    def test_sort_by_two_columns(self):
        Company.create(db.session, name="AA", isin="AA", ticker="AA")
        Company.create(db.session, name="BB", isin="CC", ticker="BB")     
        Company.create(db.session, name="BB", isin="BB", ticker="AA")
        response = self.client.get(
            url_for("rapi.company_list"),
            query_string={"sort": "name, ticker"}
        )
        data = response.json["results"]
        self.assertEqual(data[0]["name"], "AA")
        self.assertEqual(data[1]["ticker"], "AA")
        self.assertEqual(data[2]["ticker"], "BB")

    def test_for_creating_company_with_post_request(self):
        response = self.client.post(
            api.url_for(CompanyListAPI),
            data = {"name": "TEST", "isin": "TEST#ONE", "ticker": "TST" }
        )
        self.assertEqual(db.session.query(Company).count(), 1)

    def test_creates_company_with_proper_arguments(self):
        response = self.client.post(
            api.url_for(CompanyListAPI),
            data = {"name": "TEST", "isin": "TEST#ONE", "ticker": "TST" }
        )
        company = db.session.query(Company).one()
        self.assertEqual(company.name, "TEST")
        self.assertEqual(company.isin, "TEST#ONE") 

    def test_post_request_returns_400_and_error_when_no_name(self):
        response = self.client.post(
            api.url_for(CompanyListAPI),
            data = {"logo": "TEST", "isin": "TEST#ONE", "ticker": "TST" }
        ) 
        data = response.json["errors"]
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", data)

    def test_post_request_returns_400_and_error_when_no_isin(self):
        response = self.client.post(
            api.url_for(CompanyListAPI),
            data = {"name": "TEST", "isi": "TEST#ONE", "ticker": "TST" }
        ) 
        data = response.json["errors"]
        self.assertEqual(response.status_code, 400)
        self.assertIn("isin", data)

    def test_post_request_returns_400_when_not_unique_isin(self):
        comp = Company.create(db.session, name="TEST", isin="123#TEST")
        db.session.commit()
        response = self.client.post(
            api.url_for(CompanyListAPI),
            data = {"name": "TEST", "isin": "123#TEST", "ticker": "TST" }
        ) 
        data = response.json["errors"]
        self.assertEqual(response.status_code, 400)
        self.assertIn("isin", data)


class TestCompanyAPI(AppTestCase):

    def test_get_request_returns_company_data(self):
        comp = Company.create(db.session, name="TEST1", isin="#TEST1")
        db.session.commit()
        response = self.client.get(url_for("rapi.company", id=comp.id))
        data = response.json
        self.assertEqual(data["name"], comp.name)
        self.assertEqual(data["isin"], comp.isin)

    def test_get_request_returns_404_when_company_does_not_exist(self):
        db.session.commit()
        response = self.client.get(url_for("rapi.company", id=1))       
        self.assertEqual(response.status_code, 404)

    def test_for_delating_company_with_delete_request(self):
        comp = Company.create(db.session, name="TEST1", isin="#TEST1")
        db.session.commit() 
        response = self.client.delete(url_for("rapi.company", id=comp.id))
        self.assertEqual(db.session.query(Company).count(), 0)

    def test_for_updating_company_with_put_request(self):
        comp = Company.create(db.session, name="TEST1", isin="#TEST1")
        db.session.commit()
        response = self.client.put(
            url_for("rapi.company", id=comp.id),
            data={"name": "NEW NAME", "ticker": "HEJ"}
        )
        comp = db.session.query(Company).one()
        self.assertEqual(comp.name, "NEW NAME")
        self.assertEqual(comp.ticker, "HEJ")

    def test_raises_400_when_updating_with_not_unique_isin(self):
        Company.create(db.session, name="TEST1", isin="#TEST2")
        comp = Company.create(db.session, name="TEST1", isin="#TEST1")
        db.session.commit()
        response = self.client.put(
            url_for("rapi.company", id=comp.id),
            data={"name": "NEW NAME", "isin": "#TEST2"}
        )
        self.assertEqual(response.status_code, 400)
        

class TestCompanyReprListAPI(AppTestCase):

    def test_get_request_returns_json_response(self):
        comp = Company.create(db.session, name="TEST", isin="123#TEST")
        db.session.commit()
        response = self.client.get(
            api.url_for(CompanyReprListAPI, id=comp.id)
        )
        self.assertEqual(response.content_type, "application/json")

    def test_get_request_returns_404_for_non_existing_company(self):
        response = self.client.get(api.url_for(CompanyReprListAPI, id=1))
        self.assertEqual(response.status_code, 404)


class TestRecordTypeListAPI(AppTestCase):

    def test_get_request_returns_list_of_records_types(self):
        RecordType.create(db.session, name="TEST1", statement="NLS")
        RecordType.create(db.session, name="TEST2", statement="BLS")
        db.session.commit()
        response = self.client.get(api.url_for(RecordTypeListAPI))
        data = response.json["results"]
        self.assertEqual(len(data), 2)

    def test_get_request_returns_valid_data(self):
        rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
        db.session.commit()
        response = self.client.get(api.url_for(RecordTypeListAPI))
        data = response.json["results"][0]
        self.assertEqual(data["name"], rtype.name)
        self.assertEqual(data["statement"], rtype.statement)

    def test_get_request_returns_hyperlinks_to_detail_view(self):
        rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
        RecordTypeRepr.create(db.session, value="TEST Repr", lang="PL", 
                              rtype=rtype)
        db.session.commit()
        response = self.client.get(url_for("rapi.rtype_list"))
        data = response.json["results"][0]
        self.assertIsNotNone(data["uri"])
        self.assertEqual(data["uri"], url_for("rapi.rtype", id=rtype.id))

    def test_for_creating_rtype_with_post_request(self):
        response = self.client.post(
            api.url_for(RecordTypeListAPI),
            data = {"name": "TEST", "statement": "BLS"}
        )
        self.assertEqual(db.session.query(RecordType).count(), 1)

    def test_creates_rtype_with_proper_arguments(self):
        self.client.post(
            api.url_for(RecordTypeListAPI),
            data = {"name": "TEST", "statement": "BLS"}
        )
        rtype = db.session.query(RecordType).one()
        self.assertEqual(rtype.name, "TEST")
        self.assertEqual(rtype.statement, "BLS") 

    def test_post_request_returns_400_and_error_when_no_name(self):
        response = self.client.post(
            api.url_for(RecordTypeListAPI),
            data = {"wow": "TEST", "statement": "BLS"}
        )
        data = response.json["errors"]
        self.assertEqual(response.status_code, 400)
        self.assertIn("name", data)

    def test_post_request_returns_400_and_error_when_no_statement(self):
        response = self.client.post(
            api.url_for(RecordTypeListAPI),
            data = {"name": "TEST", "stm": "BLS"}
        )
        data = response.json["errors"]
        self.assertEqual(response.status_code, 400)
        self.assertIn("statement", data)


class TestRecordTypeAPI(AppTestCase):

    def test_get_request_returns_recordtype_data(self):
        rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
        db.session.commit()
        response = self.client.get(url_for("rapi.rtype", id=rtype.id))
        data = response.json
        self.assertEqual(data["name"], rtype.name)
        self.assertEqual(data["statement"], rtype.statement)

    def test_get_request_returns_404_when_rtype_does_not_exist(self):
        response = self.client.get(url_for("rapi.rtype", id=1))       
        self.assertEqual(response.status_code, 404)

    def test_for_delating_rtype_with_delete_request(self):
        rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
        db.session.commit() 
        response = self.client.delete(url_for("rapi.rtype", id=rtype.id))
        self.assertEqual(db.session.query(RecordType).count(), 0)

    def test_for_updating_rtype_with_put_request(self):
        rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
        db.session.commit()
        response = self.client.put(
            url_for("rapi.rtype", id=rtype.id), data={"statement": "BLS"}
        )
        rtype = db.session.query(RecordType).one()
        self.assertEqual(rtype.statement, "BLS")


class TestRecordTypeReprListAPI(AppTestCase):

    def create_rtype_with_reprs(self, n=2):
        rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
        for i in range(n):
            rtype.reprs.append(
                RecordTypeRepr.create(
                    db.session, 
                    value="Test Repr. #{}".format(i), lang="PL"
                )
            )
        return rtype

    def test_for_retrieving_list_of_reprs(self):
        rtype = self.create_rtype_with_reprs(n=2)
        db.session.commit()
        response = self.client.get(url_for("rapi.rtype_repr_list", id=rtype.id))
        data = response.json["results"]
        self.assertEqual(len(data), 2)

    def test_get_request_returns_correct_data(self):
        rtype = self.create_rtype_with_reprs(n=1)
        db.session.commit()
        response = self.client.get(url_for("rapi.rtype_repr_list", id=rtype.id))
        data = response.json["results"][0]
        self.assertEqual(data["value"], rtype.reprs[0].value)
        self.assertEqual(data["lang"], rtype.reprs[0].lang)  

    def test_get_request_raise_404_when_no_rtype(self):
        rtype = self.create_rtype_with_reprs(n=1)
        db.session.commit()
        response = self.client.get(
            url_for("rapi.rtype_repr_list", id=rtype.id+1)
        )
        self.assertEqual(response.status_code, 404)

    def test_for_creating_new_repr_with_post_request(self):
        rtype = self.create_rtype_with_reprs(n=0)
        db.session.commit()
        response = self.client.post(
            url_for("rapi.rtype_repr_list", id=rtype.id),
            data={"lang": "PL", "value": "NEW REPR"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(rtype.reprs.count(), 1)
        obj = rtype.reprs[0]
        self.assertEqual(obj.value, "NEW REPR")

    def test_limit_restuls_with_limit_and_offset(self):
        rtype = self.create_rtype_with_reprs(n=10)
        db.session.commit()
        response = self.client.get(
            url_for("rapi.rtype_repr_list", id=rtype.id),
            query_string={"limit": 5, "offset": 6}
        )
        data = response.json
        self.assertEqual(data["count"], 4)

    def test_order_results_with_sort_parameter(self):
        rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
        rtype.reprs.append(
            RecordTypeRepr.create(db.session, value="CC", lang="PL")
        )
        rtype.reprs.append(
            RecordTypeRepr.create(db.session, value="BB", lang="PL")
        )
        rtype.reprs.append(
            RecordTypeRepr.create(db.session, value="AA", lang="PL")
        )
        db.session.commit()

        response = self.client.get(
            url_for("rapi.rtype_repr_list", id=rtype.id),
            query_string={"sort": "value"}
        )

        data = response.json["results"]
        self.assertEqual(data[0]["value"], "AA")
        self.assertEqual(data[1]["value"], "BB")
        self.assertEqual(data[2]["value"], "CC")

    def test_sort_in_reverse_order(self):
        rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
        rtype.reprs.append(
            RecordTypeRepr.create(db.session, value="CC", lang="PL")
        )
        rtype.reprs.append(
            RecordTypeRepr.create(db.session, value="BB", lang="PL")
        )
        rtype.reprs.append(
            RecordTypeRepr.create(db.session, value="AA", lang="PL")
        )
        db.session.commit()

        response = self.client.get(
            url_for("rapi.rtype_repr_list", id=rtype.id),
            query_string={"sort": "-value"}
        )

        data = response.json["results"]
        self.assertEqual(data[0]["value"], "CC")
        self.assertEqual(data[1]["value"], "BB")
        self.assertEqual(data[2]["value"], "AA")

    def test_sort_by_two_columns(self):
        rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
        rtype.reprs.append(
            RecordTypeRepr.create(db.session, value="CC", lang="BB")
        )
        rtype.reprs.append(
            RecordTypeRepr.create(db.session, value="BB", lang="AA")
        )
        rtype.reprs.append(
            RecordTypeRepr.create(db.session, value="AA", lang="BB")
        )
        db.session.commit()

        response = self.client.get(
            url_for("rapi.rtype_repr_list", id=rtype.id),
            query_string={"sort": "lang, -value"}
        )

        data = response.json["results"]
        self.assertEqual(data[0]["value"], "BB")
        self.assertEqual(data[1]["value"], "CC")
        self.assertEqual(data[2]["value"], "AA")


class TestRecordTypeReprAPI(AppTestCase):

    def create_rtype_with_reprs(self, n=2):
        rtype = RecordType.create(db.session, name="TEST1", statement="NLS")
        for i in range(n):
            rtype.reprs.append(
                RecordTypeRepr.create(
                    db.session, 
                    value="Test Repr. #{}".format(i), lang="PL"
                )
            )
        return rtype

    def test_get_request_returns_repr_of_rtype(self):
        rtype = self.create_rtype_with_reprs(n=1)
        db.session.commit()
        response = self.client.get(
            url_for("rapi.rtype_repr", id=rtype.id, rid=rtype.reprs[0].id)
        )
        data = response.json
        self.assertEqual(data["value"], "Test Repr. #0")
        self.assertEqual(data["lang"], "PL")

    def test_put_request_updates_repr(self):
        rtype = self.create_rtype_with_reprs(n=1)
        db.session.commit()
        self.client.put(
            url_for("rapi.rtype_repr", id=rtype.id, rid=rtype.reprs[0].id),
            data={"value": "New Test Repr", "lang": "EN"}
        )
        rrepr = db.session.query(RecordTypeRepr).first()
        self.assertEqual(rrepr.lang, "EN")
        self.assertEqual(rrepr.value, "New Test Repr")

    def test_delete_request_deletes_repr(self):
        rtype = self.create_rtype_with_reprs(n=1)
        db.session.commit()
        self.client.delete(
            url_for("rapi.rtype_repr", id=rtype.id, rid=rtype.reprs[0].id),
        )
        self.assertEqual(db.session.query(RecordTypeRepr).count(), 0)
        rtype = db.session.query(RecordType).one()
        self.assertEqual(rtype.reprs.count(), 0)