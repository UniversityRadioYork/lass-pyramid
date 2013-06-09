"""Functions for working with relational database storage of metadata."""

import functools

import sqlalchemy

import lass.common.rdbms

from . import models


# Mapping of meta_types to their value column types.
# NOTE: These are lambda-delayed so that the same column isn't referenced by
# multiple metadata tables (a new column is made every time).  This would cause
# issues!
mkcolumn = functools.partial(sqlalchemy.Column, 'metadata_value')
RDBMS_COLUMNS = {
    'text': lambda: mkcolumn(sqlalchemy.Text()),
    'image': lambda: mkcolumn(sqlalchemy.String(255))
}


def metadata_from_sources(sources, date, *keys, limit=None, describe=False):
    """Runs a metadata query over 'sources' for 'key' on 'date'."""
    union = sqlalchemy.union(*sources).alias('union')

    limiter = lambda x: (x.limit(limit) if limit else x)
    executor = print if describe else lass.common.rdbms.execute

    return lass.common.rdbms.bulk_group(
        executor(limiter(metadata_from_table(union, date, keys))),
        levels=2
    )


def metadata_from_table(table, date, keys):
    """Constructs a metadata query against the given sources table."""
    key_table = models.Key.__table__
    return sqlalchemy.select(
        [
            table.c.subject_id,
            key_table.c.name.label('key'),
            table.c.value
        ],
    ).select_from(
        sqlalchemy.join(table, key_table)
    ).where(
        (key_table.c.name.in_(keys))
        & lass.common.rdbms.transient_active_on(date, table)
    ).order_by(
        sqlalchemy.asc(table.c.subject_id),
        sqlalchemy.asc(key_table.c.name),
        sqlalchemy.asc(table.c.priority),
        sqlalchemy.desc(table.c.effective_from)
    )


def direct_table(subject_table, subject_keys, meta_type, priority):
    """Creates a metadata query against a single database table.

    See 'make_metadata_table' for information about what is required of the
    query subject for this to work.

    Args:
        subject_table: The of the metadata subject, which is used to infer
            where the metadata is.
        subject_keys: The primary key of the metadata subjects (None is allowed
            if the subject supports default metadata).
        meta_type: The metadata type name.
        priority: The priority flag to attach to each record returned.
            This is used to rank metadata rows in ASCENDING order (lower
            priority flagged rows are considered first).
    Returns:
        A SQLAlchemy SELECT query against the appropriate metadata table.
    """
    table = metadata_table(subject_table, meta_type)
    subject_column = subject_of(table, subject_table)
    key_limit = (
        lambda select: select.where(
            subject_of(table, subject_table).in_(subject_keys)
        ) if subject_keys else select
    )
    return key_limit(
        sqlalchemy.sql.select(
            [
                table.c.metadata_value.label('value'),
                table.c.effective_from,
                table.c.effective_to,
                table.c.metadata_key_id,
                subject_column.label('subject_id'),
                sqlalchemy.literal(priority).label('priority')
            ]
        )
    )


def package(subject_table, subject_keys, meta_type, priority):
    # Intent: retrieve all metadata for packages, then filter down to metadata
    # joined to the subject via a package entry.
    package_entries = package_entry_table(subject_table, meta_type)
    return direct_table(
        models.Package.__table__,
        None,
        meta_type,
        priority
    ).select_from(
        sqlalchemy.join(
            models.Package.__table__,
            package_entries
        ).join(
            subject_table
        )
    )


def package_entry_table(subject_table, meta_type):
    return lass.common.rdbms.inferred_table(
        subject_table,
        namer=functools.partial(
            lass.common.rdbms.make_table_name, 'package_entry'
        ),
        creator=make_package_entry_table
    )


def subject_of(metadata_table, subject_table):
    """Given a metadata table, returns the column of the foreign key to its
    subject.
    """
    # Nasty hack, sorry
    # Returns the first foreign key that doesn't look like a fkey to Key.
    return next(
        k.parent for k in metadata_table.foreign_keys
        if k.column.table == subject_table
    )


def metadata_table(subject_table, meta_type):
    """Returns a SQLAlchemy table definition for storing the given meta_type of
    metadata in an RDBMS for the given subject class.

    See 'make_metadata_table' for information about what is required of the
    query subject for this to work.

    Args:
        subject: The Table of the element to which the metadata should be
            attached.
        meta_type: The name of the meta_type to create a table for.
    Returns:
        A sqlalchemy.Table that represents the metadata table.
    """
    return lass.common.rdbms.inferred_table(
        subject_table,
        namer=functools.partial(
            lass.common.rdbms.make_table_name, meta_type, 'metadata'
        ),
        creator=functools.partial(make_metadata_table, meta_type=meta_type)
    )


def make_package_entry_table(subject_table, table_name):
    """Creates a SQLAlchemy table definition for storing package entries
    in an RDBMS for the given subject table.

    This is a low-level constructor; you probably want 'package_entry_table'
    instead.
    """
    return lass.common.rdbms.make_attached_table(
        table_name,
        subject_table,
        models.package_foreign_key(),
        lass.common.mixins.effective_from_column(),
        lass.common.mixins.effective_to_column(),
        lass.people.mixins.approver_column(),
        lass.people.mixins.owner_column(),
        primary_key_nullable=False,
        foreign_key_nullable=True  # May need changing in some legacy tables
    )


def make_metadata_table(subject_table, meta_type, table_name):
    """Creates a SQLAlchemy table definition for storing the given meta_type of
    metadata in an RDBMS for the given subject table.

    This is a low-level constructor; you probably want 'metadata_table'
    instead.
    """
    return lass.common.rdbms.make_attached_table(
        table_name,
        subject_table,
        sqlalchemy.Column(
            'metadata_key_id',
            sqlalchemy.Integer,
            sqlalchemy.ForeignKey('metadata.metadata_key.metadata_key_id'),
        ),
        RDBMS_COLUMNS[meta_type](),
        # TODO: migrate to mixins
        lass.common.mixins.effective_from_column(),
        lass.common.mixins.effective_to_column(),
        lass.people.models.person_foreign_key(name='memberid', nullable=False),
        lass.people.models.person_foreign_key(name='approved', nullable=False),
        primary_key_nullable=False,
        foreign_key_nullable=True
    )
