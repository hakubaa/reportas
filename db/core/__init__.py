from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql.expression import ClauseElement
from sqlalchemy.ext.hybrid import hybrid_property

from .history_meta import Versioned, versioned_session
from .util import get_or_create, create, update_or_create


Base = declarative_base()


class Model(Base):
    '''Extension of base model by additional methods.'''
    __abstract__ = True

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    @classmethod
    def get_or_create(cls, session, defaults=None, **kwargs):
        obj, _ = get_or_create(session, cls, defaults, **kwargs)
        return obj

    @classmethod
    def update_or_create(cls, session, defaults=None, **kwargs):
        return update_or_create(session, cls, defaults, **kwargs)

    @classmethod
    def create(cls, session, defaults=None, **kwargs):
        return create(session, cls, defaults, **kwargs)

    def as_dict(self, exclude=list()):
        columns = set(self.__table__.columns.keys()) - set(exclude)
        return dict((col, getattr(self, col)) for col in columns)


class VersionedModel(Versioned, Model):
    __abstract__ = True

    @hybrid_property
    def history_cls(self):
        return self.__class__.__history_mapper__.class_ 


class SQLAlchemy:

    def __init__(self, *args, versioning=False, **kwargs):
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

    def create_all(self, *args, checkfirst=True, **kwargs):
        '''Create tables.'''
        Base.metadata.create_all(self.engine, *args, checkfirst=checkfirst, 
                                 **kwargs)

    def drop_all(self, *args, **kwargs):
        '''Drop all tables.'''
        Base.metadata.drop_all(self.engine, *args, **kwargs)