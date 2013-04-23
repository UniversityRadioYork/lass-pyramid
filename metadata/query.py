"""In which functions for composing and running metadata queries are found."""

import functools
import hashlib

import lass.common.rdbms

from . import rdbms


# Source helpers
def make_rdbms_source(source_func, with_default=True):
    """Creates a RDBMS-based metadata source."""
    def source(subjects, meta_type, priority):
        subject_keys = [subject.id for subject in subjects]
        return source_func(
            subject_table=lass.common.rdbms.table(subjects[0]),
            meta_type=meta_type,
            priority=priority,
            subject_keys=subject_keys + ([None] if with_default else [])
        )
    return source


own = functools.partial(make_rdbms_source, source_func=rdbms.direct_table)
package = functools.partial(make_rdbms_source, source_func=rdbms.package)


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


def run(subjects, meta_type, date, sources, *keys, describe=False):
    # Metadata is currently held in a relational database.
    # It would be spiffing to change this
    return rdbms.metadata_from_sources(
        [
            source(
                meta_type=meta_type,
                priority=priority,
                subjects=subjects
            )
            for priority, source in enumerate(sources)
        ],
        date,
        *keys,
        describe=describe
    )
