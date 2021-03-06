import operator
import datetime
import collections
from datetime import date, timedelta
from functools import reduce
import itertools
import calendar

from sqlalchemy import (
    Column, Integer, String, Boolean, Float,
    UniqueConstraint, CheckConstraint, Date, SmallInteger
)
from sqlalchemy.orm.query import Query
from sqlalchemy import func, cast, inspect, event, and_, or_, extract, select
from sqlalchemy.orm import relationship, backref, remote, foreign
from sqlalchemy.schema import ForeignKey
from sqlalchemy.dialects.postgresql import INTERVAL 
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.properties import RelationshipProperty
from dateutil.relativedelta import relativedelta

from db.core import Model, VersionedModel
from db import utils
import db.adapters.rparser as adapter


class GetDefaultReprMixin(object):

    @property
    def default_repr(self):
        return self.get_default_repr()

    def get_default_repr(self):
        reprs = self.get_reprs()
        try:
            return next(item.value for item in reprs if item.default)
        except StopIteration:
            return None

    def get_reprs(self):
        if isinstance(self.reprs, Query):
            reprs = self.reprs.all()
        else:
            reprs = self.reprs 
        return reprs


class Sector(VersionedModel):
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    def __repr__(self):
        return "<Sector({!r})>".format(self.name)

    def __str__(self):
        return self.name


class Company(VersionedModel):
    id = Column(Integer, primary_key=True)

    name = Column(String, unique=True, nullable=False)
    isin = Column(String, unique=True, nullable=False)
    ticker = Column(String)
    fullname = Column(String)
    district = Column(String)
    webpage = Column(String)
    email = Column(String)
    address = Column(String)
    debut = Column(Date)
    fax = Column(String)
    telephone = Column(String)
    fiscal_year_start_month = Column(Integer, default=1)
    sector_id = Column(Integer, ForeignKey("sector.id"))
    sector = relationship("Sector", backref=backref("companies", lazy="joined"))

    def __repr__(self):
        return "<Company({!r})>".format(self.name)

    def __str__(self):
        return self.name
        
    def determine_fiscal_year(self, start_year):
        fy_start = date(start_year, self.fiscal_year_start_month, 1)
        fy_end = fy_start + relativedelta(years=1, days=-1)
        return utils.FiscalYear(start=fy_start, end=fy_end)
        
    def determine_fiscal_months(self, timerange):
        timerange = int(timerange)
        if timerange < 1: return []
        
        months = list()
        next_month = self.fiscal_year_start_month - 1 or 12

        while next_month not in months:
            months.append(next_month)
            next_month += timerange
            if next_month > 12:
                next_month = next_month - 12

        return months
            
    @staticmethod
    def insert_companies(session):
        from scraper.util import get_info_about_companies, get_list_of_companies
        import db.tools as tools

        companies = get_list_of_companies()
        companies_db = session.query(Company.isin).all()
        if companies_db:
            companies_db = list(zip(*companies_db))[0]

        new_companies = filter(lambda cp: cp["isin"] not in companies_db, companies)
        data_companies = get_info_about_companies(
            filter(bool, map(operator.itemgetter("isin"), new_companies)),
            max_workers=5
        )

        for company in data_companies: # merge data with companies
            try:
                data = next(x for x in companies if x["isin"] == company["isin"])
            except StopIteration:
                pass
            else:
                company.update(data)

        tools.upload_companies(session, data_companies)
        session.commit()

        import rparser.specs.companies as cspec

        for comp in cspec.companies:
            company = session.query(Company).filter_by(isin=comp["isin"]).first()
            if company:
                company.reprs.append(CompanyRepr(value=comp["value"]))
        session.commit()


class CompanyRepr(VersionedModel):
    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)

    company_id = Column(Integer, ForeignKey("company.id"))
    company = relationship(
        "Company",
        backref=backref("reprs", lazy="joined", cascade="all, delete-orphan")
    )


class Report(VersionedModel):
    id = Column(Integer, primary_key=True)
    timestamp = Column(Date, nullable=False)
    timerange = Column(Integer, nullable=False)
    consolidated = Column(Boolean, default=True)
    file = Column(String)

    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    company = relationship(
        "Company",
        backref=backref("reports", lazy="joined", cascade="all, delete-orphan")
    ) 

    __table_args__ = (
    UniqueConstraint("timestamp", "timerange", "company_id", 
                    name='_timestamp_timerange_company'),
    )

    def __repr__(self):
        output = "Report({}, {}, {:%Y-%m-%d})".format(
            str(self.company), self.timerange, self.timestamp
        )
        return output

    def __str__(self):
        '''{company}: Report for {timerange} months ended on {timestamp}.'''
        output = "{}: Report for {} months ended on {:%Y-%m-%d}".format(
            str(self.company), self.timerange, self.timestamp
        )
        return output

    def add_record(self, record=None, **kwargs):
        if not record:
            record = Record(**kwargs)
        self.records.append(record)
        return record


class FinancialStatement(VersionedModel):
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    DEFAULT_FTYPES = [
        {
            "name": "bls", 
            "reprs": [
                {"default": True, "lang": "en", "value": "Balance Sheet"}
            ]
        },
        {
            "name": "ics",
            "reprs": [
                {"default": True, "lang": "en", "value": "Income Statement"}
            ]
        },
        {
            "name": "cfs",
            "reprs": [
                {"default": True, "lang": "en", "value": "Cash Flow Statement"}
            ]
        }
    ]

    def __repr__(self):
        return "FinancialStatement({!r})".format(self.name)

    def __str__(self):
        try:
            default_repr = next(filter(lambda item: item.default, self.reprs))
        except StopIteration:
            if len(self.reprs) > 0:
                return self.reprs[0].value
            else:
                return repr(self)
        return default_repr.value

    @staticmethod
    def insert_defaults(session):
        for ftype_spec in FinancialStatement.DEFAULT_FTYPES:
            ftype = FinancialStatement(name=ftype_spec["name"])
            for ftype_repr_spec in ftype_spec["reprs"]:
                ftype.reprs.append(
                    FinancialStatementRepr(**ftype_repr_spec)       
                )
            session.add(ftype)

    def get_repr(self, lang=None):
        session = inspect(self).session
        ftype_repr = session.query(FinancialStatementRepr).filter(
            func.lower(FinancialStatementRepr.lang) == func.lower(lang) 
        ).first()
        return ftype_repr

    def get_default_repr(self):
        session = inspect(self).session
        ftype_repr = session.query(FinancialStatementRepr).filter_by(
            ftype_id=self.id, default=True
        ).first()
        return ftype_repr
                

class FinancialStatementRepr(VersionedModel):
    id = Column(Integer, primary_key=True)
    value = Column(String, nullable=False)
    lang = Column(String, nullable=False, default="en")
    default = Column(Boolean, nullable=False, default=False)

    ftype_id = Column(
        Integer, ForeignKey("financialstatement.id"), nullable=False
    )
    ftype = relationship(
        "FinancialStatement", 
        backref=backref("reprs", lazy="joined", cascade="all, delete-orphan")
    )

    def __repr__(self):
        return "FinancialStatementRepr({!r}, {!r}, {!r})".format(
            self.ftype, self.lang, self.value
        )    

    def __str__(self):
        return self.value

        
class RecordType(VersionedModel):
    PIT = 1 # point-in-time (e.g. balance sheet)
    POT = 0 # period-of-time (e.g. income statement)
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    timeframe = Column(SmallInteger, nullable=False)
    
    ftype_id = Column(
        Integer, ForeignKey("financialstatement.id"), nullable=True
    )
    ftype = relationship(
        "FinancialStatement",
        backref=backref("rtypes", lazy="select", cascade="all, delete-orphan")
    )

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if other is None:
            return False
        if self.name == other.name:
            return True
        return False

    def __repr__(self):
        return "RecordType({!r})".format(self.name)

    def __str__(self):
        return self.name

    @property
    def revformulas(self):
        return [ item.formula for item in self.formula_components ]

    @staticmethod
    def insert_rtypes(session):
        import rparser.specs.records as spec
        import db.tools as tools
        tools.upload_records_spec(session, spec.finrecords)
        session.commit()


class RecordTypeRepr(VersionedModel):
    id = Column(Integer, primary_key=True)
    lang = Column(String, default="en")
    value = Column(String, nullable=False)
    default = Column(Boolean, default=False)

    rtype_id = Column(Integer, ForeignKey("recordtype.id"))
    rtype = relationship(
        "RecordType",
        backref=backref("reprs", lazy="joined", cascade="all, delete-orphan")
    )


class Timerange(Model):
    id = Column(Integer, primary_key=True)
    
    fiscal_year_start_month = Column(SmallInteger, nullable=False)
    timerange = Column(SmallInteger, nullable=False)
    month = Column(SmallInteger, nullable=False)
    
    def __repr__(self):
        return "Timerange({})".format(self.timerange) 

    @staticmethod
    def insert_defaults(
        session, timeranges=[3, 6, 12], fy_start_months=range(1, 13)
    ):
        records = Timerange.create_records(timeranges, fy_start_months)
        session.add_all(records)
        session.commit()
        
    @staticmethod
    def create_records(timeranges=[3, 6, 12], fy_start_months=range(1, 13)):
        records = []
        for timerange, fm in itertools.product(timeranges, fy_start_months):
            months = utils.determine_fiscal_months(fm, timerange)
            records.extend(
                Timerange(
                    fiscal_year_start_month=fm,
                    timerange=timerange, month=month
                )
                for month in months
            )
        return records
        
    
class Record(VersionedModel):
    id = Column(Integer, primary_key=True)
    value = Column(Float, nullable=False)
    timestamp = Column(Date, nullable=False)
    timerange = Column(Integer, nullable=False)
    synthetic = Column(Boolean, default=False, nullable=False)

    rtype_id = Column(Integer, ForeignKey("recordtype.id"), nullable=False)
    rtype = relationship(
        "RecordType",
        backref=backref("records", lazy="noload", cascade="all, delete-orphan")
    )

    report_id = Column(Integer, ForeignKey("report.id"))
    report = relationship("Report", backref=backref("records"))

    company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
    company = relationship(
        "Company",
        backref=backref("records", lazy="joined", cascade="all, delete-orphan")
    )

    __table_args__ = (
        UniqueConstraint("timestamp", "timerange", "rtype_id", "company_id", 
             name='_timestamp_timerange_rtype_company'),
    )

    def __repr__(self):
        return "<Record({!r}, {!r}, {!r})>".format(
            self.rtype, self.value, self.report
        )

    @hybrid_property
    def timestamp_start(self):
        if self.timerange == 0:
            return self.timestamp

        year = self.timestamp.year
        month = self.timestamp.month - self.timerange + 1
        if month < 1:
            year -= 1
            month = 12 + month
        return date(year, month, 1)

    @timestamp_start.expression
    def timestamp_start(cls):
        return cls.timestamp - cast("1 month", INTERVAL) * cls.timerange \
               + cast("1 day", INTERVAL) * 1

    def determine_fiscal_year(self):
        company_fy_start = self.company.fiscal_year_start_month
        timestamp = self.timestamp

        if timestamp.month < company_fy_start:
            fy_start = date(timestamp.year-1, company_fy_start, 1) 
        else:
            fy_start = date(timestamp.year, company_fy_start, 1)
        fy_end = fy_start + relativedelta(years=1, days=-1) 

        return utils.FiscalYear(start=fy_start, end=fy_end)

    def project_onto_fiscal_year(self, fiscal_year = None):
        if not fiscal_year:
            fiscal_year = self.determine_fiscal_year()

        if self.rtype.timeframe == RecordType.PIT:
            return self._project_pit_onto_fiscal_year(fiscal_year)
        else:
            return self._project_pot_onto_fiscal_year(fiscal_year)

    def _project_pit_onto_fiscal_year(self, fiscal_year):
        if self.timestamp.month >= fiscal_year.start.month:
            projection = self.timestamp.month - fiscal_year.start.month + 1
        else:
            projection = 12 - fiscal_year.start.month + self.timestamp.month + 1
        return projection, projection # return tuple just as _project_pot_onto_fiscal_year 

    def _project_pot_onto_fiscal_year(self, fiscal_year):
        if self.timestamp_start.month >= fiscal_year.start.month:
            pstart = self.timestamp_start.month - fiscal_year.start.month + 1
        else:
            pstart = 12 - fiscal_year.start.month + self.timestamp_start.month + 1
        pend = pstart + self.timerange - 1
        return pstart, pend        
    
    @staticmethod
    def create_synthetic_records(session, base_records):
        if not isinstance(base_records, collections.Iterable):
            base_records = [base_records]
        
        records_by_company = utils.group_objects(
            base_records, key=operator.attrgetter("company")
        )
        
        return utils.concatenate_lists(
            Record.create_synthetic_records_for_company(
                session, company, records
            )
            for company, records in records_by_company.items()
        )

    @staticmethod
    def create_synthetic_records_for_company(session, company, base_records):
        if not isinstance(base_records, collections.Iterable):
            base_records = [base_records]   
            
        records_by_fy = utils.group_objects(
            base_records, key=lambda item: item.determine_fiscal_year()
        )
        
        return utils.concatenate_lists(
            Record.create_synthetic_records_for_company_within_fiscal_year(
                session, company, fiscal_year, records
            )
            for fiscal_year, records in records_by_fy.items()
        )  

    @staticmethod
    def create_synthetic_records_for_company_within_fiscal_year(
        session, company, fiscal_year, base_records
    ):
        if not isinstance(base_records, collections.Iterable):
            base_records = [base_records]      
    
        formulas = utils.concatenate_lists(
            record.rtype.revformulas for record in base_records
        )
        records_db = Record.get_records_for_company_within_fiscal_year(
            session, company, fiscal_year
        )

        synthetic_records = [
            adapter.convert_rparser_record(
                session, record, company, fiscal_year
            ) 
            for record in adapter.create_synthetic_records(
                base_records, records_db, formulas
            )
        ]
        session.add_all(synthetic_records)
        return synthetic_records

    @staticmethod
    def get_records_for_company_within_fiscal_year(
        session, company, fiscal_year
    ):
        # postgre sql only
        # records = session.query(Record).filter( 
        #     Record.company == company,
        #     Record.timestamp_start >= fiscal_year.start, 
        #     Record.timestamp <= fiscal_year.end
        # ).all()
        records = session.query(Record).filter(
            Record.company == company
        ).all()
        records = list(filter(
            lambda record: record.timestamp_start >= fiscal_year.start \
                           and record.timestamp <= fiscal_year.end,
            records
        ))
        return records
        
    covered_timeranges = relationship(
        "Timerange",
        secondary="join(Company, Record, Company.id == Record.company_id)",
        primaryjoin=or_(
            and_(
                Timerange.timerange == timerange,
                remote(foreign(Timerange.month)) \
                    == extract("month", timestamp),
                remote(foreign(Timerange.fiscal_year_start_month)) \
                    == Company.fiscal_year_start_month
            ),
            and_(
                timerange == 0,
                remote(foreign(Timerange.month)) \
                    == extract("month", timestamp),
                remote(foreign(Timerange.fiscal_year_start_month)) \
                    == Company.fiscal_year_start_month,
            )
        ),
        secondaryjoin="Company.id == foreign(Record.company_id)"
    )


# timerange of 'point-in-time' records cannot be changed, this field has
# little sense for this records, because they show some value at specific
# time
@event.listens_for(Record.timerange, "set", retval=True)
def update_timerange_for_pit_records(target, value, oldvalue, initiator):
    if target.rtype and target.rtype.timeframe == RecordType.PIT:
        return 0
    return value


@event.listens_for(Record, "after_insert")
def after_insert(mapper, connection, target):
    if target.rtype and target.rtype.timeframe == RecordType.PIT:
        record_table = Record.__table__
        connection.execute(
            record_table.update().
            where(record_table.c.id == target.id).
            values(timerange=0)
        )

class RecordFormula(VersionedModel):

    id = Column(Integer, primary_key=True)
    
    rtype_id = Column(Integer, ForeignKey("recordtype.id"), nullable=False)
    rtype = relationship(
        "RecordType", backref=backref("formulas", cascade="all, delete-orphan")
    )
    
    def __repr__(self):
        cls_name = self.__class__.__name__
        right_side = self.rtype.name
        return "%s<%s, %s>" % (cls_name, right_side, self.lhs_repr())

    def lhs_repr(self):
        left_side = ''.join(
             (' - ' if component.sign == -1 else ' + ') + component.rtype.name
            for component in sorted(self.components, key=lambda x: -x.sign)
        )
        if left_side.startswith(" + "):
            left_side = left_side[3:]
        return left_side

    def __hash__(self):
        return hash(self.rtype_id) ^ \
               reduce(operator.xor, map(hash, self.components))   

    def __eq__(self, other):
        if self.rtype_id != other.rtype_id:
            return False
        if len(self.components) != len(other.components):
            return False
        for c1, c2 in zip(self.components, other.components):
            if c1 != c2:
                return False
        return True
        
    def add_component(self, component=None, **kwargs):
        if not component:
            component = FormulaComponent(**kwargs)
        self.components.append(component)
    
    def transform(self, new_lhs):
        try:
            formula_component = next(
                item for item in self.rhs if item.rtype == new_lhs
            )
        except StopIteration:
            raise RuntimeError(
                "{!r} does not appear at left hand side of "
                "the formula ".format(new_lhs)
            )

        sign_modifier = formula_component.sign * (-1)

        formula = RecordFormula(rtype=new_lhs)
        formula.add_component(
            FormulaComponent(sign=formula_component.sign, rtype=self.lhs)
        )
        formula.components.extend(
            FormulaComponent(
                sign=sign_modifier*component.sign, rtype=component.rtype
            )
            for component in self.rhs if component.rtype != new_lhs
        )
        return formula
    
    @property
    def lhs(self):
        return self.rtype
        
    @property
    def rhs(self):
        return self.components

    @staticmethod
    def insert_defaults(session):
        import rparser.specs.formulas as spec
        for lhs, rhs in spec.entity_formulas:
            rtype_lhs = session.query(RecordType).filter_by(name=lhs).one()
            formula = RecordFormula(rtype=rtype_lhs)
            session.add(formula)
            session.flush()
            for rtype_name, sign in rhs:
                rtype_rhs = session.query(RecordType)\
                                .filter_by(name=rtype_name).one()
                formula.components.append(FormulaComponent(
                    rtype=rtype_rhs, sign=sign
                ))
            session.add(formula)
        session.commit()


class FormulaComponent(VersionedModel):
    id = Column(Integer, primary_key=True)
    
    formula_id = Column(
        Integer, ForeignKey("recordformula.id"), nullable=False
    )
    formula = relationship(
        "RecordFormula",
        backref=backref("components", lazy="joined", cascade="all, delete-orphan")
    )
    
    rtype_id = Column(
        Integer, ForeignKey("recordtype.id"), nullable=False
    )
    rtype = relationship(
        "RecordType",
        backref=backref(
            "formula_components", lazy="joined", cascade="all, delete-orphan"
        )
    )
    
    sign = Column(Integer, default=1, nullable=False)
    
    __table_args__ = (
        CheckConstraint("sign in (-1, 0, 1)"),  
    )

    def __hash__(self):
        return hash(self.sign) ^ hash(self.rtype_id)

    def __eq__(self, other):
        if self.rtype_id != other.rtype_id or self.sign != other.sign:
            return False
        return True


class FinancialStatementLayout(GetDefaultReprMixin, Model):

    DEFAULT_SCHEMAS = [
        {
            "rtypes": [],
            "reprs": [
                {"lang": "PL", "value": "Pusty schema", "default": False},
                {"lang": "EN", "value": "Clear schema", "default": True}
            ],
            "inputonly": True,
            "default": False
        },
        {
            "rtypes": [ 
                "BLS@FIXEDASSETS", "BLS@CURRENTASSETS", "BLS@TOTALASSETS",
                "BLS@EQUITY", "BLS@LONGANDSHORTERMLIABILITIES", 
                "BLS@TOTALLIABILITIES"
            ],
            "reprs": [
                {"lang": "PL", "value": "Uproszczony bilans", "default": False},
                {
                    "lang": "PL", "value": "Simplify balance sheet", 
                    "default": True
                }
            ],
            "inputonly": False,
            "default": False
        },
        {
            "rtypes": [
                "ICS@REVENUESFROMSALE", "ICS@GROSSPROFITONSALES",
                "ICS@PROFITONOPERATINGACTIVITIES", "ICS@GROSSPROFIT",
                "ICS@NETPROFIT",
                "CFS@NETCFFROMOPERATINGACTIVITIES",
                "CFS@NETCFFROMINVESTMENTACTIVITIES",
                "CFS@NETCFFROMFINANCIALACTIVITIES",
                "CFS@TOTALNETCASHFLOWS",
                "BLS@TOTALASSETS", "BLS@FIXEDASSETS", "BLS@CURRENTASSETS",
                "BLS@EQUITY", "BLS@LONGTERMLIABILITIES",
                "BLS@SHORTTERMLIABILITIES"
            ],
            "reprs": [
                {"lang": "PL", "value": "Wybrane Dane Finansowe", "default": False},
                {
                    "lang": "PL", "value": "Selected Financial Data", 
                    "default": True
                }
            ],
            "inputonly": False,
            "default": True
        }
    ]

    id = Column(Integer, primary_key=True)
    inputonly = Column(Boolean, default=False)
    default = Column(Boolean, default=False)

    def append_rtype(self, rtype, position, **kwargs):
        assoc = RTypeFSchemaAssoc(
            rtype=rtype, position=position, fschema=self, **kwargs
        )
        return assoc

    def get_rtypes(self):
        return [
            {"rtype": assoc.rtype, "position": assoc.position}
            for assoc in self.rtypes
        ]

    def get_records(self, company, timerange, *, session=None):
        session = session or inspect(self).session

        rtypes = self._get_rtypes_by_timeframe()
        fiscal_months = company.determine_fiscal_months(timerange)

        pit_condition = None
        if RecordType.PIT in rtypes:
            pit_condition = and_(
                Record.rtype_id.in_(rtypes[RecordType.PIT]), 
                extract("month", Record.timestamp).in_(fiscal_months)
            )

        pot_condition = None
        if RecordType.POT in rtypes:
            pot_condition = and_(
                Record.rtype_id.in_(rtypes[RecordType.POT]),
                Record.timerange == timerange
            )

        query = session.query(Record).filter(Record.company == company)
        if pit_condition is not None and pot_condition is not None:
            query = query.filter(or_(pit_condition, pot_condition))
        elif pit_condition is not None:
            query = query.filter(pit_condition)
        elif pot_condition is not None:
            query = query.filter(pot_condition)

        return query.all()

    def _get_rtypes_by_timeframe(self):
        rtypes_by_timeframe = utils.group_objects(
            self.rtypes, key=lambda x: x.rtype.timeframe
        )
        rtypes_id_by_timeframe = {
            key: [ assoc.rtype.id for assoc in rtypes ]
            for key, rtypes in rtypes_by_timeframe.items()
        }
        return rtypes_id_by_timeframe

    @classmethod
    def insert_defaults(cls, session):
        for fschema_spec in cls.DEFAULT_SCHEMAS:
            fschema_args = { 
                cname: fschema_spec[cname] 
                for cname in cls.__table__.columns if cname in fschema_spec 
            }
            fschema = cls(**fschema_args)
            for index, rtype in enumerate(fschema_spec["rtypes"]):
                rtype_db = session.query(RecordType).filter_by(name=rtype).one()
                if rtype_db:
                    fschema.append_rtype(rtype_db, position=index)  
            for fschema_repr in fschema_spec["reprs"]:
                fschema.reprs.append(
                    FinancialStatementLayoutRepr(**fschema_repr)       
                )
            session.add(fschema)


class FinancialStatementLayoutRepr(Model):
    id = Column(Integer, primary_key=True)
    lang = Column(String, nullable=False, default="PL")
    value = Column(String, nullable=False)
    default = Column(Boolean, default=False, nullable=False)

    fschema_id = Column(
        Integer, ForeignKey("financialstatementlayout.id"), nullable=False
    )
    fschema = relationship(
        "FinancialStatementLayout",
        backref=backref("reprs", lazy="select", cascade="all, delete-orphan")
    )


class RTypeFSchemaAssoc(Model):
    '''Association table between RecordType and FinancialStatement.'''
    rtype_id = Column(Integer, ForeignKey("recordtype.id"), primary_key=True)
    fstatement_id = Column(
        Integer, ForeignKey("financialstatementlayout.id"), primary_key=True
    )
    rtype = relationship("RecordType", backref=backref("fschemas"))
    fschema = relationship("FinancialStatementLayout", backref=backref("rtypes"))
    position = Column(Integer, nullable=False, default=0)
    calculable = Column(Boolean, default=False)