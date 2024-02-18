from datetime import datetime
from sqlalchemy import *
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.orm import declarative_base

maker = sessionmaker(autoflush=True, autocommit=False)
DBSession = scoped_session(maker)
DeclarativeBase = declarative_base()
metadata = DeclarativeBase.metadata

database_setup=False
engine = None


def setup_database():
    global engine, database_setup
    if not database_setup:
        engine = create_engine('sqlite:///:memory:')
        DBSession.configure(bind=engine)
        database_setup = True


def clear_database():
    global engine, database_setup
    if not database_setup:
        setup_database()

    DBSession.rollback()
    DeclarativeBase.metadata.drop_all(engine)
    DeclarativeBase.metadata.create_all(engine)


class Thing(DeclarativeBase):
    __tablename__ = 'thing'

    uid = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(16), unique=True)


class ThingWithDate(DeclarativeBase):
    __tablename__ = 'thing_with_date'

    uid = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(Unicode(16), unique=True)
    updated_at = Column(DateTime, default=datetime.utcnow)

    related_thing_id = Column(Integer, ForeignKey('thing.uid'))
    related_thing = relationship(Thing)
