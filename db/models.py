from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.schema import ForeignKey


Base = declarative_base()


class Company(Base):
	__tablename__ = "companies"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	full_name = Column(String)
	ticker = Column(String)

	reports = relationship("Report", back_populates="company")

	def __init__(self, name, full_name=None, ticker=None):
		self.name = name
		self.short_name = short_name
		self.ticker = ticker

	def __repr__(self):
		return "<Company({!r})>".format(self.name)


class Report(Base):
	__tablename__ = "reports"

	id = Column(Integer, primary_key=True)
	timestamp = Column(DateTime, nullable=False)
	consolidated = Column(Boolean, default=True)

	company_id = Column(Integer, ForeignKey("companies.id"))
	company = relationship("Company", back_populates="reports")

	rtype_id = Column(Integer, ForeignKey("reporttypes.id"))
	rtype = relationship("ReportType", back_populates="reports")

	records = relationship("FinRecord", back_populates="report")

	def __init__(self, rtype, timestamp, consolidated=True):
		self.rtype = rtype
		self.timestamp = timestamp
		self.consolidated = consolidated

	def __repr__(self):
		return "<Report({!r}, {!r})>".format(self.rtype, self.timestamp)

	def add_record(self, record):
		self.records.append(record)


class ReportType(Base):
	__tablename__ = "reporttypes"

	id = Column(Integer, primary_key=True)
	reports = relationship("Report", back_populates="rtype")
	value = Column(String(1), nullable=False)

	def __init__(self, value):
		self.value = value

	def __repr__(self):
		return "<ReportType({!r})>".format(self.value)


class FinRecord(Base):
	__tablename__ = "finrecords"

	id = Column(Integer, primary_key=True)
	value = Column(Float, nullable=False)
	timestamp = Column(DateTime, nullable=False)
	timerange = Column(String, nullable=False)

	rtype_id = Column(Integer, ForeignKey("finrecords_dict.id"))
	rtype = relationship("FinRecordType", back_populates="records")

	report_id = Column(Integer, ForeignKey("reports.id"))
	report = relationship("Report", back_populates="records")

	def __init__(self, rtype, value, timestamp, timerange, report=None):
		self.rtype = rtype
		self.value = value
		self.timestamp = timestamp
		self.timerange = timerange
		self.report = report

	def __repr__(self):
		return "<FinRecord({!r}, {!r}, {!r})>".format(
			self.rtype, self.value, self.report
		)


class FinRecordType(Base):
	__tablename__ = "finrecords_dict"

	id = Column(Integer, primary_key=True)
	records = relationship("FinRecord", back_populates="rtype")
	name = Column(String, unique=True)
	statement = Column(String)

	def __init__(self, name, statement=None):
		self.name = name
		self.statement = statement

	@staticmethod
	def create(**kwargs):
		return FinRecordType(name=kwargs["name"], 
			                 statement=kwargs.get("statement", None))

	def __repr__(self):
		return "<FinRecordType('{!s}')>".format(self.name)


class FinRecordTypeRepr(Base):
	__tablename__ = "finrecords_repr"

	id = Column(Integer, primary_key=True)
	lang = Column(String)
	value = Column(String)

	rtype_id = Column(Integer, ForeignKey("finrecords_dict.id"))
	rtype = relationship("FinRecordType")

	def __init__(self, rtype, lang, value):
		self.rtype = rtype
		self.lang = lang
		self.value = value 

	@staticmethod
	def create(**kwargs):
		obj = FinRecordTypeRepr(rtype=kwargs["rtype"], lang=kwargs["lang"],
			                    value=kwargs["value"])
		return obj