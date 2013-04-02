from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Integer,
    String,
)

from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
)

from zope.sqlalchemy import ZopeTransactionExtension

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Person(Base):
    __tablename__ = 'member'

    id = Column('memberid', Integer, primary_key=True)

    first_name = Column('fname', String(255))
    last_name = Column('sname', String(255))
    sex = Column(Enum('m', 'f', name='sex', native_enum=False))

    local_name = Column(String(100))
    local_alias = Column(String(32))

    phone = Column(String(255))
    email = Column(String(255))
    receive_email = Column(Boolean, server_default='TRUE')

    password = Column(String(255))
    account_locked = Column(Boolean, server_default='FALSE')

    last_login = Column(DateTime())
    end_of_course = Column('endofcourse', DateTime())
    eduroam = Column(String(255))  # unlimited in DB atm
    date_joined = Column('joined', DateTime())
