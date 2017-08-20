__all__ = [
    "CompanyReprSchema", "CompanySchema", "CompanySimpleSchema", 
    "RecordTypeSchema", "RecordTypeReprSchema", "RecordTypeSimpleSchema",
    "RecordSchema", "ReportSchema", "RecordFormulaSchema",
    "FormulaComponentSchema", "SectorSchema", "FinancialStatementTypeSchema",
    "FinancialStatementTypeReprSchema", "FinancialStatementSchema",
    "FinancialStatementSchemaSimple"
]

from marshmallow import (
    validates, ValidationError, fields, validates_schema, post_load
)
from marshmallow_sqlalchemy import field_for, ModelSchema
from marshmallow.validate import OneOf
from sqlalchemy import exists, and_

import db.models as models
from db import records_factory


class MyInteger(fields.Integer):
    '''Extends Integer to not raise invalid integer for "" strings.'''

    def _format_num(self, value):
        """Return the number value for value, given this field's `num_type`."""
        if value is None or value == "":
            return None
        return self.num_type(value)


@records_factory.register_schema()
class CompanyReprSchema(ModelSchema):
    class Meta:
        model = models.CompanyRepr
        fields = ("id", "value", "company_id")

    id = MyInteger()
    company_id = field_for(
        models.CompanyRepr, "company_id", required=True,
        error_messages={"required": "Company is required."}
    )   

    @validates("company_id")
    def validate_company(self, value):
        (ret, ), = self.session.query(
            exists().where(models.Company.id == value)
        )
        if not ret:
            raise ValidationError(
                "Company with id '{}' does not exist.".format(value)
            )
        return True


@records_factory.register_schema()
class SectorSchema(ModelSchema):
    class Meta:
        model = models.Sector
        exclude = ("version",)

    @validates("name")
    def validate_name(self, value):
        if self.instance and self.instance.name == value:
            return True

        (ret, ), = self.session.query(
            exists().where(models.Sector.name == value)
        )
        if ret:
            raise ValidationError("name not unique")
        return True


@records_factory.register_schema()    
class CompanySchema(ModelSchema):
    class Meta:
        model = models.Company
        exclude = ("version",)

    id = MyInteger()
    reprs = fields.Nested(
        CompanyReprSchema, only=("id", "value"), many=True
    )
    sector = fields.Nested(SectorSchema, only=("name",), many=False)
    sector_id = field_for(models.Company, "sector_id")   

    @validates("isin")
    def validate_isin(self, value):
        if self.instance and self.instance.isin == value:
            return True

        (ret, ), = self.session.query(
            exists().where(models.Company.isin == value)
        )
        if ret:
            raise ValidationError("ISIN not unique")
        return True

    @validates("name")
    def validate_name(self, value):
        if self.instance and self.instance.name == value:
            return True

        (ret, ), = self.session.query(
            exists().where(models.Company.name == value)
        )
        if ret:
            raise ValidationError("Name not unique")
        return True

    @validates("sector_id")
    def validate_sector(self, value):
        (ret,), = self.session.query(exists().where(models.Sector.id == value))
        if not ret:
            raise ValidationError(
                "Sector with id '{}' does not exist.".format(value)
            )
        return True


class CompanySimpleSchema(ModelSchema):
    class Meta:
        model = models.Company
        fields = ("id", "isin", "name", "ticker", "uri", "fullname")

    id = MyInteger()


@records_factory.register_schema()
class FinancialStatementTypeReprSchema(ModelSchema):
    class Meta:
        model = models.FinancialStatementTypeRepr
        fields = ("id", "value", "lang", "ftype_id")

    id = MyInteger()
    ftype_id = field_for(
        models.FinancialStatementTypeRepr, "ftype_id", required=True,
        error_messages={"required": "FinancialStatementType is required."}
    )   

    @validates("ftype_id")
    def validate_rtype(self, value):
        (ret, ), = self.session.query(
            exists().where(models.FinancialStatementType.id == value)
        )
        if not ret:
            raise ValidationError(
                "FinancialStatementType with id '{}' does not exist.".format(value)
            )
        return True


@records_factory.register_schema()        
class FinancialStatementTypeSchema(ModelSchema):
    class Meta:
        model = models.FinancialStatementType
        fields = ("id", "name", "reprs")

    id = MyInteger()
    reprs = fields.Nested(
        FinancialStatementTypeReprSchema, only=("id", "value"), many=True
    )

    @validates("name")
    def validate_name(self, value):
        if self.instance and self.instance.name == value:
            return True

        (ret, ), = self.session.query(
            exists().where(models.FinancialStatementType.name == value)
        )
        if ret:
            raise ValidationError("name not unique")
        return True


@records_factory.register_schema()
class RecordTypeReprSchema(ModelSchema):
    class Meta:
        model = models.RecordTypeRepr
        fields = ("id", "value", "lang", "rtype_id")

    id = MyInteger()
    rtype_id = field_for(
        models.RecordTypeRepr, "rtype_id", required=True,
        error_messages={"required": "RecordType is required."}
    )   

    @validates("rtype_id")
    def validate_rtype(self, value):
        (ret, ), = self.session.query(
            exists().where(models.RecordType.id == value)
        )
        if not ret:
            raise ValidationError(
                "RecordType with id '{}' does not exist.".format(value)
            )
        return True
        

@records_factory.register_schema()
class RecordTypeSchema(ModelSchema):
    class Meta:
        model = models.RecordType
        exclude = ("records", "version", "revcomponents")

    id = MyInteger()
    ftype = fields.Nested(
        FinancialStatementTypeSchema, only=("name"), many=False
    )
    ftype_id = field_for(
        models.RecordType, "ftype_id", required=True,
        error_messages={"required": "FinancialStatementType is required."}
    )
    reprs = fields.Nested(
        RecordTypeReprSchema, only=("id", "value"), many=True
    )

    @validates("name")
    def validate_name(self, value):
        if self.instance and self.instance.name == value:
            return True

        (ret,), = self.session.query(
            exists().where(models.RecordType.name == value)
        )
        if ret:
            raise ValidationError("name not unique")
        return True

    @validates("ftype_id")
    def validate_ftype(self, value):
        (ret, ), = self.session.query(
            exists().where(models.FinancialStatementType.id == value)
        )
        if not ret:
            raise ValidationError(
                "FinancialStatementType with id '{}' does not " 
                "exist.".format(value)
            )
        return True


class RecordTypeSimpleSchema(ModelSchema):
    class Meta:
        model = models.RecordType
        fields = ("id", "name", "timeframe", "uri", "ftype_id")

    id = MyInteger()


@records_factory.register_schema()
class RecordSchema(ModelSchema):
    class Meta:
        model = models.Record
        exclude = ("version",)

    id = MyInteger()
    timestamp = fields.Date("%Y-%m-%d", required=True)
    rtype = fields.Nested(
        RecordTypeSchema, only=("name"), many=False
    )
    rtype_id = field_for(
        models.Record, "rtype_id", required=True,
        error_messages={"required": "RecordType is required."}
    )
    company_id = field_for(
        models.Record, "company_id", required=True,
        error_messages={"required": "Company is required."}
    )   
    report_id = field_for(models.Record, "report_id")   

    @validates("company_id")
    def validate_company(self, value):
        (ret, ), = self.session.query(
            exists().where(models.Company.id == value)
        )
        if not ret:
            raise ValidationError(
                "Company with id '{}' does not exist.".format(value)
            )
        return True

    @validates("rtype_id")
    def validate_rtype(self, value):
        (ret, ), = self.session.query(
            exists().where(models.RecordType.id == value)
        )
        if not ret:
            raise ValidationError(
                "RecordType with id '{}' does not exist.".format(value)
            )
        return True

    @validates("report_id")
    def validate_report(self, value):
        if value is None:
            return True
            
        (ret, ), = self.session.query(
            exists().where(models.Report.id == value)
        )
        if not ret:
            raise ValidationError(
                "Report with id '{}' does not exist.".format(value)
            )
        return True

    @validates_schema
    def validate_uniqueness(self, data):
        if self.instance:
            uniqnuness = self._test_uniqueness_for_update(data)
        else:
            uniqnuness = self._test_uniqueness_for_create(data)

        if not uniqnuness:
            raise ValidationError(
                "Record not unique in terms of timerange, timestamp, "
                "company and type.", field_names=("record")
            )
        return True

    def _test_uniqueness_for_update(self, data):
        # Test whether main fields can change.
        if not ("timerange" in data or "timestamp" in data 
                or "company_id" in data or "rtype_id" in data):
            return True

        timerange = data.get("timerange", self.instance.timerange)
        timestamp = data.get("timestamp", self.instance.timestamp)
        company_id = data.get("company_id", self.instance.company_id)
        rtype_id = data.get("rtype_id", self.instance.rtype_id)

        timerange = self._adjust_timerange_for_pit_records(timerange, rtype_id)

        # Test whether main fields are going to change.
        if (timerange == self.instance.timerange 
                and timestamp == self.instance.timestamp
                and company_id == self.instance.company_id
                and rtype_id == self.instance.rtype_id):
            return True

        return not self._does_record_exist(
            timerange=timerange, timestamp=timestamp, company_id=company_id,
            rtype_id=rtype_id
        )

    def _test_uniqueness_for_create(self, data):
        # Test whether fields to asses uniqueness are present.
        if not ("timerange" in data and "timestamp" in data 
                and "company_id" in data and "rtype_id" in data):
            return False

        timerange = self._adjust_timerange_for_pit_records(
            data["timerange"], data["rtype_id"]
        )

        return not self._does_record_exist(
            timerange=timerange, timestamp=data["timestamp"],
            company_id=data["company_id"], rtype_id=data["rtype_id"]
        )

    def _does_record_exist(self, timerange, timestamp, company_id, rtype_id):
        (ret, ), = self.session.query(exists().where(and_(
            models.Record.timerange == timerange,
            models.Record.timestamp == timestamp,
            models.Record.company_id == company_id,
            models.Record.rtype_id == rtype_id,
            models.Record.synthetic == False
        ))) 
        return ret

    def _adjust_timerange_for_pit_records(self, timerange, rtype_id):
        rtype = self.session.query(models.RecordType).get(rtype_id)
        if rtype and rtype.timeframe == "pit":
            return 0
        return timerange

    @post_load
    def remove_synthetic_record(self, record):
        self.session.query(models.Record).filter(
            models.Record.timerange == record.timerange,
            models.Record.timestamp == record.timestamp,
            models.Record.company_id == record.company_id,
            models.Record.rtype_id == record.rtype_id,
            models.Record.synthetic == True
        ).delete()


@records_factory.register_schema()
class ReportSchema(ModelSchema):
    class Meta:
        model = models.Report
        exclude = ("version",)  

    id = MyInteger()
    company_id = field_for(
        models.Report, "company_id", required=True,
        error_messages={"required": "Company is required."}
    ) 
    timestamp = fields.Date("%Y-%m-%d", required=True)
    records = fields.Nested(RecordSchema, many=True)

    @validates_schema
    def validate_uniqueness(self, data):
        if self.instance:
            uniqueness = self._test_uniqueness_for_update(data)
        else:
            uniqueness = self._test_uniqueness_for_create(data)

        if not uniqueness:
            raise ValidationError(
                "Report not unique in terms of timerange, timestamp and "
                "company.", field_names=("report")
            )
        return True

    def _test_uniqueness_for_update(self, data):
        if not ("timerange" in data or "timestamp" in data 
                or "company_id" in data):
            return True

        timerange = data.get("timerange", self.instance.timerange)
        timestamp = data.get("timestamp", self.instance.timestamp)
        company_id = data.get("company_id", self.instance.company_id)

        if (timerange == self.instance.timerange 
                and timestamp == self.instance.timestamp
                and company_id == self.instance.company_id):
            return True

        return not self._does_report_exist(
            timerange=timerange, timestamp=timestamp, company_id=company_id
        )

    def _test_uniqueness_for_create(self, data):
        if not ("timerange" in data and "timestamp" in data 
                and "company_id" in data):
            return False

        return not self._does_report_exist(
            timerange = data["timerange"], timestamp=data["timestamp"],
            company_id = data["company_id"]
        )

    def _does_report_exist(self, timerange, timestamp, company_id):
        (ret, ), = self.session.query(exists().where(and_(
            models.Report.timerange == timerange,
            models.Report.timestamp == timestamp,
            models.Report.company_id == company_id
        ))) 
        return ret


@records_factory.register_schema()
class FormulaComponentSchema(ModelSchema):
    class Meta:
        model = models.FormulaComponent
        exclude = ("version",)
        
    id = MyInteger()
    formula_id = field_for(
        models.FormulaComponent, "formula_id", required=True,
        error_messages={"required": "Formula is required."}
    )   
    rtype_id = field_for(
        models.FormulaComponent, "rtype_id", required=True,
        error_messages={"required": "RecordType is required."}
    )
    
    rtype = fields.Nested(RecordTypeSchema, only=("name"), many=False)
    
    @validates("rtype_id")
    def validate_rtype(self, value):
        (ret, ), = self.session.query(
            exists().where(models.RecordType.id == value)
        )
        if not ret:
            raise ValidationError(
                "RecordType with id '{}' does not exist.".format(value)
            )
        return True
        
    @validates("formula_id")
    def validate_formula(self, value):
        (ret, ), = self.session.query(
            exists().where(models.RecordFormula.id == value)
        )
        if not ret:
            raise ValidationError(
                "RecordFormula with id '{}' does not exist.".format(value)
            )
        return True 
        

@records_factory.register_schema() 
class RecordFormulaSchema(ModelSchema):
    class Meta:
        model = models.RecordFormula
        fields = ("components", "id", "rtype_id")

    id = MyInteger()
    rtype_id = field_for(
        models.RecordFormula, "rtype_id", required=True,
        error_messages={"required": "RecordType is required."}
    )   
    
    components = fields.Nested(
        FormulaComponentSchema, only=("rtype", "sign", "rtype_id"), 
        many=True
    )

    @validates("rtype_id")
    def validate_rtype(self, value):
        (ret, ), = self.session.query(
            exists().where(models.RecordType.id == value)
        )
        if not ret:
            raise ValidationError(
                "RecordType with id '{}' does not exist.".format(value)
            )
        return True


class RTypeFSchemaAssocSchema(ModelSchema):
    class Meta:
        model = models.RTypeFSchemaAssoc

    rtype_id = field_for(
        models.RTypeFSchemaAssoc, "rtype_id", required=True,
        error_messages={"required": "RecordType is required."}
    )
    rtype = fields.Nested(RecordTypeSchema, only=("id", "name"))

    @validates("rtype_id")
    def validate_rtype(self, value):
        (ret, ), = self.session.query(
            exists().where(models.RecordType.id == value)
        )
        if not ret:
            raise ValidationError(
                "RecordType with id '{}' does not exist.".format(value)
            )
        return True


@records_factory.register_schema() 
class FinancialStatementSchema(ModelSchema):
    class Meta:
        model = models.FinancialStatementSchema

    rtypes = fields.Nested(
        RTypeFSchemaAssocSchema, many=True,
        only=("position", "rtype", "calculable", "rtype_id"), 
    )


class FinancialStatementSchemaSimple(ModelSchema):
    class Meta:
        model = models.FinancialStatementSchema
        fields = ("rtypes",)

    rtypes = fields.Nested(
        RTypeFSchemaAssocSchema, only=("position", "rtype", "calculable"), 
        many=True
    )