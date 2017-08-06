__all__ = [
    "CompanyReprSchema", "CompanySchema", "CompanySimpleSchema", 
    "RecordTypeSchema", "RecordTypeReprSchema", "RecordTypeSimpleSchema",
    "RecordSchema", "ReportSchema", "RecordFormulaSchema",
    "FormulaComponentSchema", "SectorSchema", "FinancialStatementTypeSchema",
    "FinancialStatementTypeReprSchema"
]

from marshmallow import validates, ValidationError, fields, validates_schema
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
        exclude = ("records", "version", "revcomponents", "ftype_id")

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
    def validate_rtype(self, value):
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
        fields = ("id", "name", "uri", "ftype_id")

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
        (ret, ), = self.session.query(
            exists().where(models.Report.id == value)
        )
        if not ret:
            raise ValidationError(
                "Report with id '{}' does not exist.".format(value)
            )
        return True

    @validates_schema
    def validate_uniquness(self, data):
        if not ("timerange" in data and "timestamp" in data and 
                "company_id" in data and "rtype_id" in data):
            return False

        if (self.instance 
            and (
                self.instance.timerange == data["timerange"] and
                self.instance.timestamp == data["timestamp"] and
                self.instance.company_id == data["company_id"] and
                self.instance.rtype_id == data["rtype_id"]
            )
        ):
            return True

        (ret, ), = self.session.query(exists().where(and_(
            models.Record.timerange == data["timerange"],
            models.Record.timestamp == data["timestamp"],
            models.Record.company_id == data["company_id"],
            models.Record.rtype_id == data["rtype_id"]
        )))
        if ret:
            raise ValidationError(
                "Record not unique in terms of timerange, timestamp, "
                "company and type.", field_names=("record")
            )
        return True


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

    records = fields.Nested(
        RecordSchema, 
        many=True
    )

    @validates_schema
    def validate_uniquness(self, data):
        if not ("timerange" in data and "timestamp" in data and 
                "company_id" in data):
            return False

        if (self.instance 
            and (
                self.instance.timerange == data["timerange"] and
                self.instance.timestamp == data["timestamp"] and
                self.instance.company_id == data["company_id"]
            )
        ):
            return True

        (ret, ), = self.session.query(exists().where(and_(
            models.Report.timerange == data["timerange"],
            models.Report.timestamp == data["timestamp"],
            models.Report.company_id == data["company_id"]
        )))
        if ret:
            raise ValidationError(
                "Report not unique in terms of timerange, timestamp and "
                "company.", field_names=("report")
            )
        return True
    
    
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