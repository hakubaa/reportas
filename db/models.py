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
		                   back_populates="company")
	data = relationship("Record", cascade="all,delete", 
		                back_populates="company")
	reprs = relationship("CompanyRepr", cascade="all,delete", 
		                 back_populates="company")

	def __repr__(self):
		return "<Company({!r})>".format(self.name)


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

	data = relationship("Record", cascade="all,delete", 
		                back_populates="report")

	__table_args__ = (
    	UniqueConstraint("timestamp", "timerange", "company_id", 
    		             name='_timestamp_timerange_company'),
    )

	def __repr__(self):
		return "<Report({!r}, {!r})>".format(self.timestamp, self.timerange)

	def add_record(self, record=None, **kwargs):
		if not record:
			record = Record(**kwargs)
		self.data.append(record)
		return record


class Record(Model):
	__tablename__ = "records"

	id = Column(Integer, primary_key=True)
	value = Column(Float, nullable=False)
	timestamp = Column(DateTime, nullable=False)
	timerange = Column(Integer, nullable=False)

	rtype_id = Column(Integer, ForeignKey("records_dic.id"))
	rtype = relationship("RecordType", back_populates="records")

	report_id = Column(Integer, ForeignKey("reports.id"))
	report = relationship("Report", back_populates="data")

	company_id = Column(Integer, ForeignKey("companies.id"))
	company = relationship("Company", back_populates="data")

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

	records = relationship("Record", back_populates="rtype")
	reprs = relationship("RecordTypeRepr", back_populates="rtype")

	def __repr__(self):
		return "<RecordType('{!s}')>".format(self.name)


class RecordTypeRepr(Model):
	__tablename__ = "records_repr"

	id = Column(Integer, primary_key=True)
	lang = Column(String)
	value = Column(String)

	rtype_id = Column(Integer, ForeignKey("records_dic.id"))
	rtype = relationship("RecordType", back_populates="reprs")