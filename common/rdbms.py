"""Common helper functions for lower-level database access.

Unless stated otherwise, these functions use URY database conventions:

    1) Database names are singular with the exception of 'XYZ_metadata'.
    2) Database names are lowercase_underscored.
    3) Names have no app prefix (use PostgreSQL schemata instead).
    4) Primary keys are table_name_id...
    5) ...as are unambiguous foreign keys to other tables.
"""

import collections
import itertools

import sqlalchemy

import lass.model_base


NAMEABLES_EQUAL_GETTERS = {
    str: lambda table, key: table.c.name == key,
    int: lambda table, key: primary_key_of(table) == key,
    object: lambda table, key: primary_key_of(table) == key.id,
}


def in_if_defined(column, xs):
    """Returns 'column in xs' if xs is truthy, else True."""
    return column.in_(xs) if xs else True


def bulk_group(tuples, levels=2):
    """Given an iterable of tuples, recursively groups the tuples into
    dicts until the final item of each tuple is thusly grouped.

    The result is a dictionary of either nested dictionaries or lists, depending
    on when 'levels' nesting levels is reached; the lists will contain only
    one of each element, but in the order that the tuples existed in the
    original list.
    
    This is most useful for assembling database results into hierarchies, for
    example grouping metadata by subject/key or credits by subject/type.

    NOTE: The grouping elements MUST be ordered.
    """
    assert(levels > 0)

    result = collections.defaultdict(dict if levels > 1 else list)
    grouped = itertools.groupby(tuples, lambda x: x[0])

    for group, raw_groupees in grouped:
        # The groupees still have the group as index 0 in their tuple,
        # let's remove it and flatten the tuple if possible
        groupees = (
            (groupee[1] if len(groupee) == 2 else groupee[1:])
            for groupee in raw_groupees
        )
        if levels > 1:
            result[group] = bulk_group(groupees, levels=levels - 1)
        else:
            result[group] = remove_duplicates(groupees)
    return result
    

def remove_duplicates(xs):
    # Inefficient but works on non-hashables (including lists).
    unique = []
    for x in xs:
        if x not in unique:
            unique.append(x)
    return unique


def execute(*args, **kwargs):
    """Wrapper around the 'execute' method of LASS's configured database
    engine.
    """
    return engine().execute(*args, **kwargs)


def engine():
    """Retrieves LASS's configured database engine for non-ORM querying."""
    # This is an awful hack.
    return lass.model_base.DBSession.bind


def table(subject):
    """Retrieves the table of a SQLAlchemy ORM model."""
    return subject.__table__


def foreign_key_to_table(table, *args, **keywords):
    """Given a table with exactly one primary key, constructs a foreign key
    column referencing it.
    """
    return foreign_key_from(primary_key_of(table), *args, **keywords)


def foreign_key_from(column, *args, **keywords):
    """Given a 'Column', constructs a foreign key column referencing it,
    using URY convention.

    *args and **keywords are passed to the 'Column' constructor, with the
    exception of the keyword argument 'name' which, if present, overrides the
    inferred column name for the foreign key..
    """
    return sqlalchemy.Column(
        # v-- URY convention for unambiguous foreign keys
        keywords.pop('name', column.name),
        keywords.pop('type_', column.type),
        sqlalchemy.ForeignKey(column),
        *args,
        **keywords
    )


def infer_primary_key(table_name, *args, **keywords):
    """Given a table name and optional Column arguments, creates a primary key
    column for that table using URY conventions.
    """
    return sqlalchemy.Column(
        infer_id_name(table_name),
        sqlalchemy.Integer,
        primary_key=True,
        *args,
        **keywords
    )


def primary_key_of(table):
    """Returns the Column representing the SINGLE primary key of a table.

    This will fail if the table has a composite key, or no primary key.
    """
    # Need to have one and only one primary key on the subject for this to work
    # (o/` I am the one and only o/`)

    pkeys = table.primary_key.columns.values()
    if len(pkeys) != 1:
        raise ValueError('Subject must have exactly one primary key.')
    return pkeys[0]


def infer_id_name(table_name):
    """Infers the name of the table's primary key column using URY convention.

    >>> infer_id_name('troll')
    'troll_id'
    """
    return '_'.join((table_name, 'id'))


def make_table_name(*parts, subject_table_name=''):
    """Given name parts, constructs a table name per URY convention.

    If 'subject_table_name' is given, it is placed before the other arguments.
    This is for convenience when using this as a namer for 'inferred_table'.

    >>> make_table_name('fus', 'ro', 'dah', subject_table_name='dovahkiin')
    'dovahkiin_fus_ro_dah'
    """
    return '_'.join([subject_table_name] + [part.lower() for part in parts])


def to_full_name(schema, table_name):
    """Converts 'table_name' to a full name by appending its schema.

    >>> to_full_name(None, 'jujus')
    'jujus'

    >>> to_full_name('cherubim', 'jujus')
    'cherubim.jujus'

    Args:
        schema: The name of the schema, or a falsy value if the table is not
            in a schema.
        table_name: The unqualified name of the table.
    Returns:
        The schema-qualified ('full') table name, if a schema exists.
    """
    return '.'.join((schema, table_name)) if schema else table_name


def transient_active_on(date, transient):
    """Constructs a check to filter the table 'transient' (with columns
    'effective_from' and 'effective_to') down to only those rows active on
    'date'.
    """
    null = None  # stop static analysis checkers from moaning about == None
    return sqlalchemy.between(
        date,
        transient.c.effective_from,
        sqlalchemy.case(
            [
                # NULL effective_to => always on past effective_from
                (transient.c.effective_to == null, date),
                (transient.c.effective_to != null, transient.c.effective_to)
            ]
        )
    )


def inferred_table(subject_table, namer, creator):
    """Creates or gets a table whose name and other properties are 'inferred'
    from another table.

    Args:
        subject_table: The table of the subject of the inference.
        namer: A callable taking the subject table's name (as keyword argument
            'subject_table_name', IMPORTANT) and returning the inferred table's
            name.
        creator: A callable taking the subject table, inferred table's name and
            the SQLAlchemy MetaData of the current context, and returning a
            Table
    Returns:
        A Table as created by 'creator' and named by 'namer' with respect to
        'subject_table'.
    """
    table_name = namer(subject_table_name=subject_table.name)

    return create_or_get_table(
        subject_table.metadata.tables,
        to_full_name(subject_table.schema, table_name),
        lambda: creator(subject_table=subject_table, table_name=table_name)
    )


def create_or_get_table(tables, name, creator):
    """Gets the named table if it exists in the SQL metadata, or creates it.

    Args:
        tables: The dict of tables currently stored in the SQLAlchemy MetaData
            that the table is expected to lie within.  ('MetaData.tables')
        name: The full table name (including any schema).
        creator: A delayed computation (0-argument function) that, when called,
            will create the table and add it to 'sa_meta'.
    Returns:
        The table, either retrieved from 'sa_meta' or created with 'creator'.

    >>> create_or_get_table({'table': 'placeholder'}, 'table', None)
    'placeholder'

    >>> create_or_get_table({}, 'table', lambda: 'created')
    'created'
    """
    return ((lambda: tables[name]) if name in tables else creator)()


def make_attached_table(
    table_name, subject_table, *columns,
    primary_key_nullable=False,
    foreign_key_nullable=True
):
    """Creates a table that is 'attached' to another table.

    This is shorthand for making a URY-conventions table named 'table_name',
    with a foreign key back to 'subject_table' and the given columns.  The
    table inherits its schema and SQLAlchemy metadata from 'subject_table'.

    Note that the table must not already exist in the metadata.  See
    'get_or_create_table' for a workaround.
    """
    return sqlalchemy.schema.Table(
        table_name,
        subject_table.metadata,
        infer_primary_key(table_name, nullable=primary_key_nullable),
        foreign_key_to_table(subject_table, nullable=foreign_key_nullable),
        *columns,
        schema=subject_table.schema
    )


def find_foreign_key_to(column, source_table, target_table):
    """Given 'column' in 'target_table', attempts to find a foreign key in
    'source_table' that references it.
    """
    column_name = '.'.join((target_table.fullname, column.name))
    try:
        return next(
            fkey for fkey in source_table.foreign_keys
            if fkey.target_fullname == column.name
        )
    except StopIteration:
        raise ValueError(
            'No foreign key in {} references {}.'.format(
                source_table.fullname,
                column_name
            )
        )
