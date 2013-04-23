"""Common mixins for LASS models."""

import sqlalchemy


description_column = sqlalchemy.Column(
    """Mixin for models with a description."""
    'description',
    sqlalchemy.Text(),
    nullable=False
)
effective_from_column = sqlalchemy.Column(
    'effective_from',
    sqlalchemy.DateTime(timezone=True)
)
effective_to_column = sqlalchemy.Column(
    'effective_to',
    sqlalchemy.DateTime(timezone=True)
)
name_column = sqlalchemy.Column(
    'name',
    sqlalchemy.String(50),
    nullable=False
)


transient_columns = effective_from_column, effective_to_column


class Described(object):
    """Mixin for models whose items have a description.

    This is intended mainly for describing things like categories and types;
    generally you will want to use metadata for most describable items.
    """
    description = description_column


class Named(object):
    """Mixin for models whose items have an internal name."""
    name = name_column

    def __str__(self):
        return self.name


class Submittable(object):
    """Mixin for models that record a submitted date."""
    submitted_at = sqlalchemy.Column(
        'submitted',
        sqlalchemy.DateTime(timezone=True),
        nullable=True  # Not submitted/no submission recorded
    )


class Transient(object):
    """Mixin for models representing data with a potentially limited lifespan.
    """
    effective_from = effective_from_column
    effective_to = effective_to_column


class Type(Named, Described):
    pass
