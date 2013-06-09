"""Database-specific functions for the people submodule of the URY website.

This module contains functions that rely on directly bashing the database
in a relational manner.

Notably, most of the heavy lifting of the credits system is contained here,
because credits work on a relational level (similar to metadata).
"""

import functools

import sqlalchemy

import lass.common
import lass.people


def bulk_credits(
    subject_table,
    subject_ids,
    date,
    *types
):
    """Returns credits for the given subject table and primary keys.
    
    Args:
        subject_table: The SQLAlchemy Table representing the subject data of the
            credits query.
        subject_ids: A list of primary keys indexing the subject table, for
            whom credits will be retrieved.
        date: The date to use when deciding which credits are relevant.  This
            will usually be the current date.
        types: The names of the credit types ('Presenter', 'Producer' etc) to
            which the credit search should be limited to.  If no types are
            given, all credits will be returned.
    """
    return lass.common.rdbms.bulk_group(
        lass.common.rdbms.execute(
            credits_select(
                subject_table,
                subject_ids,
                date,
                types,
            )
        ),
        levels=2
    )


def credits_select(subject_table, subject_ids, date, types):
    """Runs a SELECT query for credits on a given subject table and IDs."""
    credits = credits_table(subject_table)
    people = lass.common.rdbms.table(lass.people.models.Person)
    ctypes = lass.common.rdbms.table(lass.people.models.CreditType)
    subject_pk = lass.common.rdbms.primary_key_of(subject_table).label(
        'subject'
    )
    return sqlalchemy.select(
        [
            subject_pk,
            ctypes.c.name,
            people.c.fname.label('first_name'),
            people.c.sname.label('last_name'),
            ctypes.c.plural,
            ctypes.c.is_in_byline,
        ]
    ).select_from(
        sqlalchemy.join(subject_table, credits).join(ctypes).join(
            people,
            onclause=credits.c.creditid == people.c.memberid
        )
    ).where(
        (subject_pk.in_(subject_ids))
        & (lass.common.rdbms.in_if_defined(ctypes.c.name, types))
        & (lass.common.rdbms.transient_active_on(date, credits))
    ).order_by(
        sqlalchemy.asc(subject_pk),
        sqlalchemy.asc(ctypes.c.name),
        sqlalchemy.asc(people.c.sname),
        sqlalchemy.asc(people.c.fname)
    )


def credits_table(subject_table):
    """Returns a credits table given a credit subject table."""
    return lass.common.rdbms.inferred_table(
        subject_table,
        namer=functools.partial(
            lass.common.rdbms.make_table_name, 'credit'
        ),
        creator=make_credits_table
    )


def make_credits_table(subject_table, table_name):
    """Creates a SQLAlchemy table definition for storing credits in a RDBMS
    for the given subject table.
    """
    return lass.common.rdbms.make_attached_table(
        table_name,
        subject_table,
        lass.common.rdbms.infer_primary_key(table_name),
        lass.common.rdbms.foreign_key_to_table(subject_table),
        lass.common.rdbms.foreign_key_to_table(
            lass.people.models.CreditType.__table__
        ),
        lass.people.models.person_foreign_key(name='creditid'),
        lass.common.mixins.effective_from_column(),
        lass.common.mixins.effective_to_column(),
        lass.people.mixins.owner_column(),
        lass.people.mixins.approver_column(),
    )
