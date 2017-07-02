import operator

from sqlalchemy import (
	Column, Integer, String, DateTime, Boolean, Float,
	UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey

from db.core import Model


class Company(Model):
	__tablename__ = "companies"

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

	reports = relationship("Report", cascade="all,delete",
		                   back_populates="company", lazy="dynamic")
	records = relationship("Record", cascade="all,delete", 
		                back_populates="company", lazy="dynamic")
	reprs = relationship("CompanyRepr", cascade="all,delete", 
		                 back_populates="company", lazy="joined")

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

		import parser.cspec as cspec

		for comp in cspec.companies:
			company = session.query(Company).filter_by(isin=comp["isin"]).one()
			company.reprs.append(
				CompanyRepr(value=comp["value"])
			)
		session.commit()


class CompanyRepr(Model):
	__tablename__ = "companyrepr"

	id = Column(Integer, primary_key=True)
	value = Column(String)

	company_id = Column(Integer, ForeignKey("companies.id"))
	company = relationship("Company", back_populates="reprs")


class Report(Model):
	__tablename__ = "reports"

	id = Column(Integer, primary_key=True)
	timestamp = Column(DateTime, nullable=False)
	timerange = Column(Integer, nullable=False)
	consolidated = Column(Boolean, default=True)

	company_id = Column(Integer, ForeignKey("companies.id"))
	company = relationship("Company", back_populates="reports")

	records = relationship("Record", cascade="all,delete", 
		                back_populates="report", lazy="noload")

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


class Record(Model):
	__tablename__ = "records"

	id = Column(Integer, primary_key=True)
	value = Column(Float, nullable=False)
	timestamp = Column(DateTime, nullable=False)
	timerange = Column(Integer, nullable=False)

	rtype_id = Column(Integer, ForeignKey("records_dic.id"), nullable=False)
	rtype = relationship("RecordType", back_populates="records", lazy="joined")

	report_id = Column(Integer, ForeignKey("reports.id"))
	report = relationship("Report", back_populates="records")

	company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
	company = relationship("Company", back_populates="records", lazy="joined")

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


class RecordType(Model):
    __tablename__ = "records_dic"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    statement = Column(String, nullable=False)

    records = relationship("Record", back_populates="rtype", lazy="dynamic")
    reprs = relationship("RecordTypeRepr", back_populates="rtype", 
    lazy="dynamic")

    __table_args__ = (
        CheckConstraint("statement in ('nls', 'bls', 'cfs')"),  
    )

    def __repr__(self):
        return "<RecordType('{!s}')>".format(self.name)

    @staticmethod
    def insert_rtypes(session):
        import parser.spec as spec
        import db.util as util
        util.upload_records_spec(session, spec.finrecords)
        session.commit()


class RecordTypeRepr(Model):
	__tablename__ = "records_repr"

	id = Column(Integer, primary_key=True)
	lang = Column(String)
	value = Column(String)

	rtype_id = Column(Integer, ForeignKey("records_dic.id"))
	rtype = relationship("RecordType", back_populates="reprs", lazy="joined")