from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from .util import get_or_create, create

Base = declarative_base()


class Model(Base):
	'''Extension of base model by additional methods.'''
	__abstract__ = True
	
	@classmethod
	def get_or_create(cls, session, defaults=None, **kwargs):
		obj, _ = get_or_create(session, cls, defaults, **kwargs)
		return obj

	@classmethod
	def create(cls, session, defaults=None, **kwargs):
		return create(session, cls, defaults, **kwargs)


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

	def drop_all(self, *args, **kwargs):
		'''Drop all tables.'''
		Base.metadata.drop_all(self.engine, *args, **kwargs)
