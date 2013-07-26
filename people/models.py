"""Models and related helpers for the membership database."""

import sqlalchemy

import lass.model_base
import lass.common.mixins
import lass.people.mixins
import lass.metadata.mixins


class Person(lass.model_base.Base):
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
        sqlalchemy.Enum('m', 'f', name='sex', native_enum=False)
    )

    # A lot of fields below were present in the member table but are not
    # part of the model for security purposes.

    #local_name = sqlalchemy.Column(sqlalchemy.String(100))
    #local_alias = sqlalchemy.Column(sqlalchemy.String(32))

    #phone = sqlalchemy.Column(sqlalchemy.String(255))
    #email = sqlalchemy.Column(sqlalchemy.String(255))
    #receive_email = sqlalchemy.Column(
    #    sqlalchemy.Boolean,
    #    server_default='TRUE'
    #)

    #account_locked = sqlalchemy.Column(
    #    sqlalchemy.Boolean,
    #    server_default='FALSE'
    #)

    #last_login = sqlalchemy.Column(sqlalchemy.DateTime)
    #end_of_course = sqlalchemy.Column('endofcourse', sqlalchemy.DateTime)
    #eduroam = sqlalchemy.Column('eduroam', sqlalchemy.String(255))
    date_joined = sqlalchemy.Column('joined', sqlalchemy.DateTime)
