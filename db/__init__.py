from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


class SQLAlchemy:

	def __init__(self, *args, **kwargs):
		self.engine = create_engine(*args, **kwargs)
		self._session = None

	@property
	def session(self):
		if not self._session:
			Session = sessionmaker(bind=self.engine)
			self._session = Session()
		return self._session

	def create_all(self, *args, **kwargs):
		'''Create tables.'''
		Base.metadata.create_all(self.engine, *args, **kwargs)

	def drop_all(self):
		'''Drop all tables.'''
		Base.metadata.drop_all(self.engine, *args, **kwargs)
