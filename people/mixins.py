import collections
import datetime

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
owner_column = lambda: models.person_foreign_key(
    name='memberid',
    nullable=False
)


class Creditable(object):
    """Mixin for items that have credits."""
    @classmethod
    def add_credits(
        cls,
        items,
        *types,
        date=None,
        attr='credits',
        with_byline_attr=None
    ):
        """Annotates a set of items with their credits.

        This is a bulk credit query operation (one credits query per call).

        Args:
            items: The items to annotate.  These MUST be instances of 'cls'.
            *types: The type names of credits to fetch metadata for.  If no
                types are provided, all types are returned.
            date: The date (as a datetime) on which the retrieved credits should
                be active. (Default: see 'bulk_credits')
            attr: The name of the attribute on the items in which the
                credits dictionary will be stored.  (Default: 'credits')
            with_byline_attr: If a string, then the by-line for each item will
                be computed and stored in the attribute of that name.  (Default:
                disabled)
        """
        if items:
            lass.common.utils.annotate(
                items,
                cls.bulk_credits(items, *types, date=date),
                attribute_name=attr
            )
            if with_byline_attr:
                bylines = collections.defaultdict(list)
                for item in items:
                    setattr(
                        item,
                        with_byline_attr,
                        [
                            credit for credits in (
                                group
                                for group in getattr(item, attr).values()
                            ) for credit in credits
                        ]
                    )

            
    @classmethod
    def bulk_credits(cls, subjects, *types, date=None):
        return lass.people.rdbms.bulk_credits(
            lass.common.rdbms.table(cls),
            [subject.id for subject in subjects],
            (
                date if date
                else datetime.datetime.now(datetime.timezone.utc)
            ),
            *types
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


class Ownable(object):
    """Mixins for models that are ownable by people."""
    @sqlalchemy.ext.declarative.declared_attr
    def owner_id(cls):
        return owner_column()

    @sqlalchemy.ext.declarative.declared_attr
    def owner(cls):
        return sqlalchemy.orm.relationship(
            'Person',
            primaryjoin='Person.id == {}.owner_id'.format(cls.__name__)
        )


class PersonSubmittable(
    Ownable,
    lass.common.mixins.Submittable
):
    """Mixins for models that are submittable by people (their owners)."""
    pass
