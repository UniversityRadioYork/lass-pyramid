"""The data models for the Credits submodule of the URY website.

These data models are implemented using SQLAlchemy and contain no
website-specific code, and are theoretically transplantable into any Python
project.

Most notably missing from these models is any semblance of a "get URL" function
as this is defined at the template level.  This is not ideal, but is
deliberately done to separate data models from the website concepts.

---

Copyright (c) 2013, University Radio York.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import sqlalchemy

import lass.model_base
import lass.common.mixins
import lass.metadata.models


class CreditType(lass.model_base.Base, lass.common.mixins.Named):
    """A type of credit."""
    __tablename__ = 'credit_type'
    __table_args__ = {'schema': 'people'}

    id = sqlalchemy.Column(
        'credit_type_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )
    plural = sqlalchemy.Column(sqlalchemy.String(255), nullable=False)
    is_in_byline = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        server_default='FALSE'
    )

    def __lt__(self, other):
        """Determines whether this credit type is less than another.

        This method is implemented so that types can be sorted by name
        directly.
        """
        return self.name < other.name


class Credit(lass.metadata.models.Attachable):
    """Abstract model for credits, to be extended for each creditable."""
    __abstract__ = True
    backref = 'credits'

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

