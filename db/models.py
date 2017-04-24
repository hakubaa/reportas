from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String


Base = declarative_base()


class Company:
	__tablename__ ="companies"

	id = Column(Integer, primary_key=True)
	name = Column(String)
	#short_name = Column(String)
	#ticker = Column(String)

	def __init__(self, name):#, short_name=None, ticker=None):
		self.name = name
		#self.short_name = short_name
		#self.ticker = ticker

	def __repr__(self):
		return "<Company('{!r}')>".format(self.name)