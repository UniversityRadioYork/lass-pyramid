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

import lass.common.time


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
    def active_in_range(self, start, finish):
        """Checks whether this transient was active at any point
        between 'start' and 'finish'.
        """
        null = None  # Stop static analysis from complaining about == None
        return (
            self.started_by(finish) & self.not_finished_by(start)
       )

    @sqlalchemy.ext.hybrid.hybrid_method
    def contains(self, date):
        """Checks whether 'date' is inside the range of this transient."""
        return (
            self.started_by(date) & self.not_finished_by(date)
        )

    @sqlalchemy.ext.hybrid.hybrid_method
    def started_by(self, date):
        """Is true when a transient has become effective on or before
        the given date.
        """
        return (
            (self.effective_from is not None) and self.effective_from <= date
        )

    @started_by.expression
    def started_by(cls, date):
        """The SQL expression version of 'started_by'."""
        null = None  # Stop static analysis from complaining about == None
        return (cls.effective_from != null) & (cls.effective_from <= date)

    @sqlalchemy.ext.hybrid.hybrid_method
    def not_finished_by(self, date):
        """Is true if a transient has not stopped becoming effective on
        or after the given date.
        """
        # Must be separate because | doesn't short-circuit.
        return (self.effective_to is None) or date <= self.effective_to

    @not_finished_by.expression
    def not_finished_by(cls, date):
        """The SQL expression version of 'not_finished_by'."""
        null = None  # Stop static analysis from complaining about == None
        return (cls.effective_to == null) | (date <= cls.effective_to)



    @sqlalchemy.ext.hybrid.hybrid_method
    def contains_submitted_at(self, _):
        """Checks whether this transient is active for an object whose
        submission date is 'submitted_at'.
        """
        null = None  # Stop static analysis from complaining about == None

        # Ignore the submission date, because at the moment an active
        # transient on a submission date is one that is currently
        # active with respect to now.
        return self.not_finished_by(lass.common.time.aware_now())

    @sqlalchemy.ext.hybrid.hybrid_method
    def contains_object(self, object):
        """Checks an arbitrary object to see if it fits inside the
        range of this transient.
        """
        # Try a multitude of methods to figure out the appropriate
        # way of comparing this object.

        if hasattr(object, 'submitted_at'):
            cmp = self.contains_submitted_at(object.submitted_at)
        elif hasattr(object, 'start') and hasattr(object, 'finish'):
            cmp = self.active_in_range(object.start, object.finish)
        else:
            cmp = True
        return cmp


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
