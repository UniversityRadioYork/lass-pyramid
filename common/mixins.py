"""Common mixins for LASS models."""

import sqlalchemy


# Column generators for inclusion in non-ORM SQL.
# Note that these MUST be lambda'd to prevent the same column being used in
# multiple models/tables.
description_column = lambda: sqlalchemy.Column(
    'description',
    sqlalchemy.Text(),
    nullable=False
)
effective_from_column = lambda: sqlalchemy.Column(
    'effective_from',
    sqlalchemy.DateTime(timezone=True)
)
effective_to_column = lambda: sqlalchemy.Column(
    'effective_to',
    sqlalchemy.DateTime(timezone=True)
)
name_column = lambda: sqlalchemy.Column(
    'name',
    sqlalchemy.String(50),
    nullable=False
)
submitted_at_column = lambda: sqlalchemy.Column(
    'submitted',
    sqlalchemy.DateTime(timezone=True),
    nullable=True  # Not submitted/no submission recorded
)


transient_columns = lambda: effective_from_column(), effective_to_column()


class Described(object):
    """Mixin for models whose items have a description.

    This is intended mainly for describing things like categories and types;
    generally you will want to use metadata for most describable items as
    Described does not implement history.
    """
    description = description_column()


class Named(object):
    """Mixin for models whose items have an internal name."""
    name = name_column()

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


class Type(Named, Described):
    pass
