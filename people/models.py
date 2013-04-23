"""Models and related helpers for the membership database."""

import sqlalchemy

import lass.common.rdbms


def person_foreign_key(*args, **keywords):
    """Defines a foreign key to a 'Person'.

    To specify the column name, supply 'name' as a keyword argument; otherwise
    the name will be inferred from 'Person.id'.
    """
    return lass.common.rdbms.foreign_key_from(
        Person.id,
        *args,
        **keywords
    )


class Person(lass.Base):
    """A person in the membership database."""
    __tablename__ = 'member'

    id = sqlalchemy.Column(
        'memberid',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )

    first_name = sqlalchemy.Column('fname', sqlalchemy.String(255))
    last_name = sqlalchemy.Column('sname', sqlalchemy.String(255))
    sex = sqlalchemy.Column(
        'sex',
        sqlalchemy.Enum('m', 'f', name='sex', native_enum=False)
    )

    local_name = sqlalchemy.Column(sqlalchemy.String(100))
    local_alias = sqlalchemy.Column(sqlalchemy.String(32))

    phone = sqlalchemy.Column(sqlalchemy.String(255))
    email = sqlalchemy.Column(sqlalchemy.String(255))
    receive_email = sqlalchemy.Column(
        sqlalchemy.Boolean,
        server_default='TRUE'
    )

    password = sqlalchemy.Column(sqlalchemy.String(255))
    account_locked = sqlalchemy.Column(
        sqlalchemy.Boolean,
        server_default='FALSE'
    )

    last_login = sqlalchemy.Column(sqlalchemy.DateTime)
    end_of_course = sqlalchemy.Column('endofcourse', sqlalchemy.DateTime)
    eduroam = sqlalchemy.Column('eduroam', sqlalchemy.String(255))
    date_joined = sqlalchemy.Column('joined', sqlalchemy.DateTime)
