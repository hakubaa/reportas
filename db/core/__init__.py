from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.expression import ClauseElement

from .util import get_or_create, create


Base = declarative_base()


class Model(Base):
	'''Extension of base model by additional methods.'''
	__abstract__ = True

	def __init__(self, **kwargs):
		cls = self.__class__
		valid_fields = cls.__mapper__.columns.keys() +\
					   cls.__mapper__.relationships.keys()

		for key, value in kwargs.items():
			if not isinstance(value, ClauseElement) and key in valid_fields:
				setattr(self, key, value)

	@classmethod
	def get_or_create(cls, session, defaults=None, **kwargs):
		obj, _ = get_or_create(session, cls, defaults, **kwargs)
		return obj

	@classmethod
	def create(cls, session, defaults=None, **kwargs):
		return create(session, cls, defaults, **kwargs)

	def as_dict(self, exclude=list()):
		columns = set(self.__table__.columns.keys()) - set(exclude)
		return dict((col, getattr(self, col)) for col in columns)


class SQLAlchemy:

	def __init__(self, *args, **kwargs):
		self.engine = create_engine(*args, **kwargs)
		self.session = self.create_session()
		
	@contextmanager
	def session_scope(self, new_session=True):
		if new_session:
			session = self.create_session()
		else:
			session = self.session

		try:
			yield session
			session.commit()
		except:
			session.rollbakc()
			raise
		finally:
			session.close()

	def create_session(self):
	    '''Create the session factory.'''
	    Session = sessionmaker(bind=self.engine)
	    return Session()

	def create_all(self, *args, **kwargs):
		'''Create tables.'''
		Base.metadata.create_all(self.engine, *args, **kwargs)

	def drop_all(self, *args, **kwargs):
		'''Drop all tables.'''
		Base.metadata.drop_all(self.engine, *args, **kwargs)