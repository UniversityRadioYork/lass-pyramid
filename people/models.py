"""Models and related helpers for the membership database."""

import sqlalchemy

import lass.model_base
import lass.common.mixins
import lass.people.mixins


class CreditType(lass.model_base.Base, lass.common.mixins.Named):
    """A type of credit."""
    __tablename__ = 'credit_type'
    __table_args__ = {'schema': 'people'}

    id = sqlalchemy.Column(
        'credit_type_id',
        sqlalchemy.Integer(),
        primary_key=True,
        nullable=False
    )
    plural = sqlalchemy.Column(sqlalchemy.String(length=255), nullable=False)
    is_in_byline = sqlalchemy.Column(
        sqlalchemy.Boolean(),
        nullable=False,
        server_default='FALSE'
    )


class Credit(
    sqlalchemy.ext.declarative.AbstractConcreteBase,
    lass.model_base.Base,
    lass.common.mixins.Transient,
    lass.people.mixins.Ownable,
    lass.people.mixins.Approvable
):
    """Abstract model for credits, to be extended for each creditable."""
    @sqlalchemy.ext.declarative.declared_attr
    def credit_type_id(cls):
        return sqlalchemy.Column(
            sqlalchemy.ForeignKey(
                'people.credit_type.credit_type_id'
            )
        )

    @sqlalchemy.ext.declarative.declared_attr
    def type(cls):
        return sqlalchemy.orm.relationship('CreditType', lazy='joined')

    @sqlalchemy.ext.declarative.declared_attr
    def person_id(cls):
        return sqlalchemy.Column(
            'creditid',
            sqlalchemy.ForeignKey('member.memberid')
        )

    @sqlalchemy.ext.declarative.declared_attr
    def person(cls):
        return sqlalchemy.orm.relationship(
            'Person',
            lazy='joined',
            primaryjoin='Person.id == {}.person_id'.format(cls.__name__)
        )


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
