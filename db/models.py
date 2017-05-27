from sqlalchemy import (
	Column, Integer, String, DateTime, Boolean, Float,
	UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey

from db.core import Model
import db.core.util as util


class Company(Model):
	__tablename__ = "companies"

	id = Column(Integer, primary_key=True)
	
	name = Column(String)
	isin = Column(String, unique=True)
	ticker = Column(String, unique=True)
	fullname = Column(String)
	district = Column(String)
	webpage = Column(String)
	email = Column(String)
	address = Column(String)
	debut = Column(DateTime)
	fax = Column(String)
	telephone = Column(String)
	sector = Column(String)

	reports = relationship("FinReport", cascade="all,delete",
		                   back_populates="company")
	data = relationship("FinRecord", cascade="all,delete", 
		                back_populates="company")
	reprs = relationship("CompanyRepr", cascade="all,delete", 
		                 back_populates="company")

	__table_args__ = (
		UniqueConstraint("isin", "ticker", name='_isin_ticker'),
    )

	def __repr__(self):
		return "<Company({!r})>".format(self.name)


class CompanyRepr(Model):
	__tablename__ = "companyrepr"

	id = Column(Integer, primary_key=True)
	value = Column(String)

	company_id = Column(Integer, ForeignKey("companies.id"))
	company = relationship("Company", back_populates="reprs")


class FinReport(Model):
	__tablename__ = "reports"

	id = Column(Integer, primary_key=True)
	timestamp = Column(DateTime, nullable=False)
	timerange = Column(Integer, nullable=False)
	consolidated = Column(Boolean, default=True)

	company_id = Column(Integer, ForeignKey("companies.id"))
	company = relationship("Company", back_populates="reports")

	data = relationship("FinRecord", cascade="all,delete", 
		                back_populates="report")

	__table_args__ = (
    	UniqueConstraint("timestamp", "timerange", "company_id", 
    		             name='_timestamp_timerange_company'),
    )

	def __repr__(self):
		return "<FinReport({!r}, {!r})>".format(self.timestamp, self.timerange)

	def add_record(self, record=None, **kwargs):
		if not record:
			record = FinRecord(**kwargs)
		self.data.append(record)
		return record


class FinRecord(Model):
	__tablename__ = "finrecords"

	id = Column(Integer, primary_key=True)
	value = Column(Float, nullable=False)
	timestamp = Column(DateTime, nullable=False)
	timerange = Column(Integer, nullable=False)

	rtype_id = Column(Integer, ForeignKey("finrecords_dict.id"))
	rtype = relationship("FinRecordType", back_populates="records")

	report_id = Column(Integer, ForeignKey("reports.id"))
	report = relationship("FinReport", back_populates="data")

	company_id = Column(Integer, ForeignKey("companies.id"))
	company = relationship("Company", back_populates="data")

	__table_args__ = (
    	UniqueConstraint("timestamp", "timerange", "rtype_id", "company_id", 
    		             name='_timestamp_timerange_rtype_company'),
    )

	def __repr__(self):
		return "<FinRecord({!r}, {!r}, {!r})>".format(
			self.rtype, self.value, self.report
		)

	@classmethod
	def create_or_update(cls, session, rtype, value, timestamp, timerange,
			             report, company, defaults=None, override=False):
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


class FinRecordType(Model):
	__tablename__ = "finrecords_dict"

	id = Column(Integer, primary_key=True)
	records = relationship("FinRecord", back_populates="rtype")
	name = Column(String, unique=True)
	statement = Column(String)

	def __repr__(self):
		return "<FinRecordType('{!s}')>".format(self.name)


class FinRecordTypeRepr(Model):
	__tablename__ = "finrecords_repr"

	id = Column(Integer, primary_key=True)
	lang = Column(String)
	value = Column(String)

	rtype_id = Column(Integer, ForeignKey("finrecords_dict.id"))
	rtype = relationship("FinRecordType")