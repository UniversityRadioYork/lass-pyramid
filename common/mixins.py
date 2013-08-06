"""Common mixins for LASS models.

---

Copyright (c) 2013, University Radio York.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import sqlalchemy
import sqlalchemy.ext.hybrid


class Described(object):
    """Mixin for models whose items have a description.

    This is intended mainly for describing things like categories and
    types; generally you will want to use metadata for most describable
    items as Described does not implement history.
    """
    description = sqlalchemy.Column(sqlalchemy.Text, nullable=False)

class Named(object):
    """Mixin for models whose items have an internal name."""
    name = sqlalchemy.Column(sqlalchemy.String(50), nullable=False)

    def __str__(self):
        return self.name


class Submittable(object):
    """Mixin for models that record a submitted date."""
    submitted_at = sqlalchemy.Column(
        'submitted',
        sqlalchemy.DateTime(timezone=True),
        nullable=True  # Not submitted/no submission recorded
    )

    @sqlalchemy.ext.hybrid.hybrid_property
    def start(self):
        """Alias for 'submitted_at' for compatibility with other items which
        have a start date.
        """
        return self.submitted_at

    @sqlalchemy.ext.hybrid.hybrid_property
    def duration(self):
        return self.effective_to - self.effective_from


class Transient(object):
    """Mixin for models representing data with a potentially limited lifespan.
    """
    effective_from = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))
    effective_to = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))

    @sqlalchemy.ext.hybrid.hybrid_property
    def start(self):
        """Alias for 'effective_from' for compatibility with other items which
        have a start date.
        """
        return self.effective_from

    @sqlalchemy.ext.hybrid.hybrid_property
    def duration(self):
        return self.effective_to - self.effective_from

    @sqlalchemy.ext.hybrid.hybrid_method
    def contains(self, date):
        """Checks whether 'date' is inside the range of this transient."""
        null = None  # Stop static analysis from complaining about == None
        return (
            (self.effective_from != null) &
            (self.effective_from <= date) &
            (
                (self.effective_to == null) |
                (self.effective_to > date)
            )
        )

    @classmethod
    def active_on(cls, date, transient=None):
        """Constructs a check to filter the table 'transient' (with columns
        'effective_from' and 'effective_to') down to only those rows active on
        'date'.

        Args:
            date: The datetime on which the transient must be active.
            transient: If given, the table, column set or model whose transient
                columns will be checked; if None, the class from which this
                method was called will be the transient.  (Default: None.)

        Returns:
            A SQLAlchemy expression implementing the transient activity check.
        """
        null = None  # stop static analysis checkers from moaning about == None

        if transient is None:
            transient = cls

        return sqlalchemy.between(
            date,
            transient.effective_from,
            sqlalchemy.case(
                [
                    # NULL effective_to => always on past effective_from
                    (transient.effective_to == null, date),
                    (transient.effective_to != null, transient.effective_to)
                ]
            )
        )


class Type(Named, Described):
    pass
