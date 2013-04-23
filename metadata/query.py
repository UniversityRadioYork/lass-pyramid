"""In which functions for composing and running metadata queries are found."""

import functools
import hashlib

import lass.common.rdbms

from . import rdbms


# Source helpers
def make_rdbms_source(source_func, subject, sub_key):
    """Creates a RDBMS-based metadata source."""
    return functools.partial(
        rdbms.direct_table,
        sub_table=lass.common.rdbms.table(subject),
        sub_key=sub_key
    )


def own(subject):
    """Creates a source for querying the given subject's own metadata."""
    return make_rdbms_source(rdbms.direct_table, subject, subject.id)


def default(subject):
    """Creates a source for querying the subject type's default metadata."""
    return make_rdbms_source(rdbms.direct_table, subject, None)


def package(subject):
    """Creates a source for querying any packages attached to the subject."""
    return make_rdbms_source(rdbms.package, subject, subject.id)


def default_package(subject):
    """Creates a source for querying the subject type's default packages."""
    return make_rdbms_source(rdbms.package, subject, None)


def cache_key(subject, meta_type, key, date):
    """
    Returns a representation of the query that can be used as a
    cache key.

    Returns:
        a string that represents the query in a way that is sufficiently unique
        for caching purposes.
    """
    # This used to be a human-readable string, but given memcached's
    # rather stringent key requirements it's easier to just bung all
    # the information that makes queries unique (and only that information)
    # in a hash.
    h = hashlib.md5()
    components = [
        subject.__class__,
        subject.id,
        meta_type,
        key,
        date,
    ]
    for c in components:
        h.update(repr(c).encode())
    return h.hexdigest()


def run(subject, meta_type, date, sources, *keys, describe=False):
    # Metadata is currently held in a relational database.
    # It would be spiffing to change this
    return rdbms.metadata_from_sources(
        [
            source(meta_type=meta_type, priority=priority)
            for priority, source in enumerate(sources)
        ],
        date,
        *keys,
        describe=describe
    )
