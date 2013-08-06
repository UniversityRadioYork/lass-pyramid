"""Functions for composing and running metadata queries and searches.

---

Copyright (c) 2013, University Radio York.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import collections
import functools
import itertools
import sqlalchemy

import lass.common.time
import lass.metadata.models


def relationship(model, type):
    """Returns the model's relationship to a given attached metadata
    type, or None if none exists.
    """
    return getattr(model, type + '_entries', None)


def relationship_to_model(rel):
    """Converts a relationship reference to the model of its target."""
    return sqlalchemy.inspection.inspect(rel).mapper.class_


def own(subjects, meta_type, priority):
    """Queries for all metadata attached to a given set of subjects, for
    a given type of metadata.
    """
    meta_entries = relationship(subjects[0].__class__, meta_type)

    if meta_entries is not None:
        meta_model = relationship_to_model(meta_entries)

        query = all_metadata(meta_model, priority).filter(
            meta_model.subject_id.in_([subject.id for subject in subjects])
        )
    else:
        query = None
    return query


def package(subjects, meta_type, priority):
    """Queries for all metadata attached to a given set of subjects, for
    a given type of metadata and indirected through the metadata package
    layer.
    """
    package_entries = relationship(subjects[0].__class__, 'package')
    package_meta_entries = relationship(lass.metadata.models.Package, meta_type)

    if package_entries is not None and package_meta_entries is not None:
        package_entry_model = relationship_to_model(package_entries)
        meta_model = relationship_to_model(package_meta_entries)

        query = all_metadata(meta_model, priority).join(
            package_entry_model.package,
        ).filter(
            package_entry_model.subject_id.in_(
                [subject.id for subject in subjects]
            )
        )
    else:
        query = None
    return query


def all_metadata(meta_model, priority):
    """Creates a query pulling all metadata from a metadata model.

    This query can be used as the base for more refined metadata
    queries.

    Args:
        meta_model: The model containing the metadata.
        priority: An integer representing the priority of this metadata
            source in a metadata query (lower numbers are considered
            before higher ones).

    Returns:
        A query returning all metadata in 'meta_model', in the form
        (key name, value, effective from, effective to, subject ID,
        priority).
    """
    return lass.model_base.DBSession.query(
        lass.metadata.models.Key.name.label('key'),
        meta_model.value.label('value'),
        meta_model.effective_from.label('effective_from'),
        meta_model.effective_to.label('effective_to'),
        meta_model.subject_id.label('subject_id'),
        sqlalchemy.literal(priority).label('priority')
    ).select_from(
        meta_model
    ).join(
        lass.metadata.models.Key
    )

    
def run(subjects, meta_type, date, sources, *keys):
    # Metadata is currently held in a relational database.
    # It would be spiffing to change this
    first, *rest = itertools.filterfalse(
        lambda s: s is None,
        (
            source(subjects, meta_type, priority)
            for priority, source in enumerate(sources)
        )
    )

    union = first.union(*rest).subquery()

    return bulk_group(
        lass.model_base.DBSession.query(
            union.c.subject_id,
            union.c.key,
            union.c.value
        ).filter(
            (union.c.key.in_(keys)) &
            (lass.common.mixins.Transient.active_on(date, union.c))
        ).order_by(
            sqlalchemy.asc(union.c.subject_id),
            sqlalchemy.asc(union.c.key),
            sqlalchemy.asc(union.c.priority),
            sqlalchemy.desc(union.c.effective_from)
        )
    )


def bulk_group(tuples, levels=2):
    """Given an iterable of tuples, recursively groups the tuples into
    dicts until the final item of each tuple is thusly grouped.

    The result is a dictionary of either nested dictionaries or lists,
    depending on when 'levels' nesting levels is reached; the lists will
    contain only one of each element, but in the order that the tuples
    existed in the original list.

    This is most useful for assembling database results into
    hierarchies, for example grouping metadata by subject/key or credits
    by subject/type.

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


def search(term, keys, model, now=None, order='alpha'):
    """Constructs a metadata search query.

    Args:
        term: A string to search for; at time of writing, this will be
            searched for as a case-insensitive string fragment.
        keys: A list of names of metadata keys in which 'term' should be
            searched for.
        model: The model, whose textual metadata is in 'text_entries',
            whose metadata is to be searched and to which type the
            results should belong.
        now: The time at which the metadata retrieved should be active.
            If None, the current time is used.  (Default: None.)
        order: The ordering to use; either alphabetical ('alpha') or
            chronologically from most recent ('recent').
            (Default: 'alpha'.)

    Returns:
        A query returning a list of instances of 'model' for which one
        or more items of current metadata contain 'term', or None if
        there is not enough information available for a search (either
        'term' was empty, or no 'keys' were provided).

    """
    if now is None:
        now = lass.common.time.aware_now()
 
    # This is needed to force the backreferences on model that point to its
    # metadata to appear.  Any less hacky way of doing this is much appreciated.
    _ = model()

    meta = relationship_to_model(model.text_entries)

    if term and keys:
        query = lass.model_base.DBSession.query(
            model
        ).join(
            model.text_entries
        ).filter(
            (meta.contains(now)) &
            (meta.value.ilike("%{}%".format(term))) &
            meta.key.has(lass.metadata.models.Key.name.in_(keys))
        ).order_by(
            meta.value if order == 'alpha' else model.start.desc()
        )

        assert query is not None, 'Got None for a query with term and keys.'
    else:
        query = None

    return query


def searchable_keys():
    """Finds all metadata keys that should be available for searching.

    This function costs one database query per run.

    Returns:
        A list of metadata keys, in alphabetical order by their plural
        name, that are allowed to be specified as fields in a metadata
        based search.
    """
    return lass.model_base.DBSession.query(
        lass.metadata.models.Key
    ).filter(
        lass.metadata.models.Key.searchable
    ).order_by(
        sqlalchemy.asc(lass.metadata.models.Key.plural)
    ).all()
