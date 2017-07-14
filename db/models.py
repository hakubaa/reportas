import operator

from sqlalchemy import (
	Column, Integer, String, DateTime, Boolean, Float,
	UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import ForeignKey

from db.core import Model, VersionedModel


class Company(VersionedModel):
	id = Column(Integer, primary_key=True)
	
	name = Column(String, nullable=False)
	isin = Column(String, unique=True, nullable=False)
	ticker = Column(String)
	fullname = Column(String)
	district = Column(String)
	webpage = Column(String)
	email = Column(String)
	address = Column(String)
	debut = Column(DateTime)
	fax = Column(String)
	telephone = Column(String)
	sector = Column(String)

	def __repr__(self):
		return "<Company({!r})>".format(self.name)

	@staticmethod
	def insert_companies(session):
		from scraper.util import get_info_about_companies, get_list_of_companies
		import db.util as util

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

		util.upload_companies(session, data_companies)
		session.commit()

		import rparser.cspec as cspec

		for comp in cspec.companies:
			company = session.query(Company).filter_by(isin=comp["isin"]).one()
			company.reprs.append(
				CompanyRepr(value=comp["value"])
			)
		session.commit()


class CompanyRepr(VersionedModel):
	id = Column(Integer, primary_key=True)
	value = Column(String, nullable=False)

	company_id = Column(Integer, ForeignKey("company.id"))
	company = relationship(
		"Company", 
		backref=backref("reprs", lazy="joined", cascade="all, delete")
	)


class Report(VersionedModel):
	id = Column(Integer, primary_key=True)
	timestamp = Column(DateTime, nullable=False)
	timerange = Column(Integer, nullable=False)
	consolidated = Column(Boolean, default=True)

	company_id = Column(Integer, ForeignKey("company.id"))
	company = relationship(
		"Company", 
		backref=backref("reports", lazy="dynamic", cascade="all,delete")
	) 

	__table_args__ = (
    	UniqueConstraint("timestamp", "timerange", "company_id", 
    		             name='_timestamp_timerange_company'),
    )

	def __repr__(self):
		return "<Report({!r}, {!r})>".format(self.timestamp, self.timerange)

	def add_record(self, record=None, **kwargs):
		if not record:
			record = Record(**kwargs)
		self.records.append(record)
		return record


class RecordType(VersionedModel):
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    statement = Column(String, nullable=False)

    __table_args__ = (
        CheckConstraint("statement in ('nls', 'bls', 'cfs')"),  
    )

    def __repr__(self):
        return "<RecordType('{!s}')>".format(self.name)

    @staticmethod
    def insert_rtypes(session):
        import rparser.spec as spec
        import db.util as util
        util.upload_records_spec(session, spec.finrecords)
        session.commit()


class RecordTypeRepr(VersionedModel):
	id = Column(Integer, primary_key=True)
	lang = Column(String, default="PL")
	value = Column(String, nullable=False)

	rtype_id = Column(Integer, ForeignKey("recordtype.id"))
	rtype = relationship("RecordType", backref=backref("reprs", lazy="joined"))

	
class Record(VersionedModel):
	id = Column(Integer, primary_key=True)
	value = Column(Float, nullable=False)
	timestamp = Column(DateTime, nullable=False)
	timerange = Column(Integer, nullable=False)
	synthetic = Column(Boolean, default=False, nullable=False)

	#dependencies
    #impacts

	rtype_id = Column(Integer, ForeignKey("recordtype.id"), nullable=False)
	rtype = relationship(
		"RecordType", backref=backref("records", lazy="joined")
	)

	report_id = Column(Integer, ForeignKey("report.id"))
	report = relationship("Report", backref=backref("records"))

	company_id = Column(Integer, ForeignKey("company.id"), nullable=False)
	company = relationship(
		"Company", backref=backref("records", lazy="joined")
	)

	__table_args__ = (
    	UniqueConstraint("timestamp", "timerange", "rtype_id", "company_id", 
    		             name='_timestamp_timerange_rtype_company'),
    )

	def __repr__(self):
		return "<Record({!r}, {!r}, {!r})>".format(
			self.rtype, self.value, self.report
		)

	@classmethod
	def create_or_update(cls, session, rtype, value, timestamp, timerange,
			             report, company, defaults=None, override=False):
		import db.util as util
		obj, newly_created = util.get_or_create(
			session, cls, defaults={"value": value, "report": report},
			rtype=rtype, timestamp=timestamp, timerange=timerange,
			company=company
		)
		if ((override or report.timestamp > obj.report.timestamp)
			and not newly_created
		):
			obj.report = report
			obj.value = value

		return obj


class RecordFormula(VersionedModel):
    id = Column(Integer, primary_key=True)
    
    rtype_id = Column(Integer, ForeignKey("recordtype.id"), nullable=False)
    rtype = relationship(
        "RecordType", backref=backref("formulas", lazy="dynamic")
    )
    
    def __repr__(self):
        cls_name = self.__class__.__name__
        right_side = self.rtype.name
        left_side = ''.join(
             (' - ' if component.sign == -1 else ' + ') + component.rtype.name
            for component in self.components
        )
        if left_side.startswith(" + "):
            left_side = left_side[3:]
        return "%s<%s, %s>" % (cls_name, right_side, left_side)
        
    def add_component(self, component=None, **kwargs):
        if not component:
            component = FormulaComponent(**kwargs)
        self.components.append(component)
    

class FormulaComponent(VersionedModel):
    id = Column(Integer, primary_key=True)
    
    formula_id = Column(
        Integer, ForeignKey("recordformula.id"), nullable=False
    )
    formula = relationship(
        "RecordFormula", backref=backref("components", lazy="joined")
    )
    
    rtype_id = Column(
        Integer, ForeignKey("recordtype.id"), nullable=False
    )
    rtype = relationship(
        "RecordType", backref=backref("revformulas", lazy="joined")
    )
    
    sign = Column(Integer, default=1, nullable=False)
    
    __table_args__ = (
        CheckConstraint("sign in (-1, 0, 1)"),  
    )