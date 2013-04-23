"""Functions for working with relational database storage of metadata."""

import collections
import functools

import sqlalchemy

import lass.common.rdbms

from . import models


# Mapping of meta_types to their value column types.
RDBMS_COLUMNS = {
    'text': sqlalchemy.Column('metadata_value', sqlalchemy.Text()),
    'image': sqlalchemy.Column('metadata_value', sqlalchemy.String(255))
}


def metadata_from_sources(sources, date, *keys, limit=None, describe=False):
    """Runs a metadata query over 'sources' for 'key' on 'date'."""
    union = sqlalchemy.union(*sources).alias('union')

    limiter = lambda x: (x.limit(limit) if limit else x)
    executor = print if describe else lass.common.rdbms.execute

    return to_dict(executor(limiter(metadata_from_table(union, date, keys))))


def to_dict(results):
    """Converts a metadata query results set into a dict-like object."""
    results_dict = collections.defaultdict(list)
    for key, value in results:
        results_dict[key].append(value)
    return results_dict


def metadata_from_table(table, date, keys):
    """Constructs a metadata query against the given sources table."""
    key_table = models.Key.__table__
    return sqlalchemy.select(
        [
            key_table.c.name.label('key'),
            table.c.value
        ],
    ).select_from(
        sqlalchemy.join(table, key_table)
    ).where(
        (key_table.c.name.in_(keys))
        & lass.common.rdbms.transient_active_on(date, table)
    ).order_by(
        sqlalchemy.asc(key_table.c.name),
        sqlalchemy.asc(table.c.priority),
        sqlalchemy.desc(table.c.effective_from)
    )


def direct_table(sub_table, sub_key, meta_type, priority):
    """Creates a metadata query against a single database table.

    See 'make_metadata_table' for information about what is required of the
    query subject for this to work.

    Args:
        sub_table: The of the metadata subject, which is used to infer
            where the metadata is.
        sub_key: The primary key of the metadata subject, which may be
            different from the subject's actual key (for example, when looking
            for default metadata)
        meta_type: The metadata type name.
        priority: The priority flag to attach to each record returned.
            This is used to rank metadata rows in ASCENDING order (lower
            priority flagged rows are considered first).
    Returns:
        A SQLAlchemy SELECT query against the appropriate metadata table.
    """
    table = metadata_table(sub_table, meta_type)
    return sqlalchemy.sql.select(
        [
            table.c.metadata_value.label('value'),
            table.c.effective_from,
            table.c.effective_to,
            table.c.metadata_key_id,
            sqlalchemy.literal(priority).label('priority')
        ]
    ).where(
        subject_of(table, sub_table) == sub_key
    )


def package(sub_table, sub_key, meta_type, priority):
    # Intent: retrieve all metadata for packages, then filter down to metadata
    # joined to the subject via a package entry.
    package_meta = direct_table(
        models.package.Package.__table__,
        sub_key,
        meta_type,
        priority
    )
    package_entries = package_entry_table(sub_table, meta_type)

    return lass.common.rdbms.indirect_join(
        package_meta,
        package_entries,
        sub_table
    )


def package_entry_table(sub_table, meta_type):
    return lass.common.rdbms.inferred_table(
        sub_table,
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


def metadata_table(sub_table, meta_type):
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
        sub_table,
        namer=functools.partial(
            lass.common.rdbms.make_table_name, meta_type, 'metadata'
        ),
        creator=functools.partial(make_metadata_table, meta_type=meta_type)
    )


def make_package_entry_table(sub_table, table_name):
    """Creates a SQLAlchemy table definition for storing package entries
    in an RDBMS for the given subject table.

    This is a low-level constructor; you probably want 'package_entry_table'
    instead.
    """
    return lass.common.rdbms.make_attached_table(
        table_name,
        sub_table,
        models.package.package_foreign_key(),
        lass.common.mixins.effective_from_column,
        lass.common.mixins.effective_to_column,
        lass.people.models.person_foreign_key('memberid', nullable=False),
        lass.people.models.person_foreign_key('approved', nullable=False),
        primary_key_nullable=False,
        foreign_key_nullable=True  # May need changing in some legacy tables
    )


def make_metadata_table(sub_table, meta_type, table_name):
    """Creates a SQLAlchemy table definition for storing the given meta_type of
    metadata in an RDBMS for the given subject table.

    This is a low-level constructor; you probably want 'metadata_table'
    instead.
    """
    return lass.common.rdbms.make_attached_table(
        table_name,
        sub_table,
        sqlalchemy.Column(
            'metadata_key_id',
            sqlalchemy.Integer,
            sqlalchemy.ForeignKey('metadata.metadata_key.metadata_key_id'),
        ),
        RDBMS_COLUMNS[meta_type],
        # TODO: migrate to mixins
        lass.common.mixins.effective_from_column,
        lass.common.mixins.effective_to_column,
        lass.people.models.person_foreign_key(name='memberid', nullable=False),
        lass.people.models.person_foreign_key(name='approved', nullable=False),
        primary_key_nullable=False,
        foreign_key_nullable=True
    )
