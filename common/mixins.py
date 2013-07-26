"""Common mixins for LASS models."""

import sqlalchemy

import lass.model_base


# Column generators for inclusion in non-ORM SQL.
# Note that these MUST be lambda'd to prevent the same column being used in
# multiple models/tables.
effective_from_column = lambda: sqlalchemy.Column(
    'effective_from',
    sqlalchemy.DateTime(timezone=True)
)
effective_to_column = lambda: sqlalchemy.Column(
    'effective_to',
    sqlalchemy.DateTime(timezone=True)
)
submitted_at_column = lambda: sqlalchemy.Column(
    'submitted',
    sqlalchemy.DateTime(timezone=True),
    nullable=True  # Not submitted/no submission recorded
)


class Described(object):
    """Mixin for models whose items have a description.

    This is intended mainly for describing things like categories and types;
    generally you will want to use metadata for most describable items as
    Described does not implement history.
    """
    description = sqlalchemy.Column(
        sqlalchemy.Text,
        nullable=False
    )

class Named(object):
    """Mixin for models whose items have an internal name."""
    name = sqlalchemy.Column(
        sqlalchemy.String(50),
        nullable=False
    )

    def __str__(self):
        return self.name


class Submittable(object):
    """Mixin for models that record a submitted date."""
    submitted_at = submitted_at_column()


class Transient(object):
    """Mixin for models representing data with a potentially limited lifespan.
    """
    effective_from = effective_from_column()
    effective_to = effective_to_column()

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
