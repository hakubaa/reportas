import datetime

from sqlalchemy import (
	Column, Integer, String, DateTime, Boolean, Float,
	UniqueConstraint
)

from db.core import Model

class File(Model):
	__tablename__ = "files"

	id = Column(Integer, primary_key=True)
	name = Column(String(), unique=True)
	timestamp = Column(DateTime, default=datetime.datetime.utcnow)

	def __repr__(self):
		return "<File %r>" % self.name


