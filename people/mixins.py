import sqlalchemy

import lass.common.mixins

from . import models


# Column generators for inclusion in non-ORM SQL.
# Note that these MUST be lambda'd to prevent the same column being used in
# multiple models/tables.
approver_column = lambda: models.person_foreign_key(
    name='approvedid',
    nullable=False
)
submitter_column = lambda: models.person_foreign_key(
    name='memberid',
    nullable=False
)


class Approvable(object):
    """Mixin for items that must be approved before becoming usable."""
    @sqlalchemy.ext.declarative.declared_attr
    def approver_id(cls):
        return approver_column()

    @sqlalchemy.ext.declarative.declared_attr
    def approver(cls):
        return sqlalchemy.orm.relationship(
            'Person',
            primaryjoin='Person.id == {}.approver_id'.format(cls.__name__)
        )


class PersonSubmittable(lass.common.mixins.Submittable):
    """Mixins for models that are submittable by people."""
    @sqlalchemy.ext.declarative.declared_attr
    def submitter_id(cls):
        return submitter_column()

    @sqlalchemy.ext.declarative.declared_attr
    def submitter(cls):
        return sqlalchemy.orm.relationship(
            'Person',
            primaryjoin='Person.id == {}.submitter_id'.format(cls.__name__)
        )
