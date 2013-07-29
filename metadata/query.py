"""In which functions for composing and running metadata queries are found."""

import collections
import functools
import itertools
import sqlalchemy

import lass.common.time
import lass.metadata.models


def relationship(model, type):
    """Returns the model's relationship to a given attached metadata type, or
    None if none exists.
    """
    return getattr(model, type + '_entries', None)


def relationship_to_model(rel):
    """Converts a relationship reference to the model of its target."""
    return sqlalchemy.inspection.inspect(rel).mapper.class_


def own(subjects, meta_type, priority):
    """Queries for all metadata attached to a given set of subjects, for a
    given type of metadata."""
    meta_entries = relationship(subjects[0].__class__, meta_type)

    if meta_entries is not None:
        meta_model = relationship_to_model(meta_entries)

        query = lass.model_base.DBSession.query(
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
        ).filter(
            meta_model.subject_id.in_([subject.id for subject in subjects])
        )
    else:
        query = None
    return query


def package(subjects, meta_type, priority):
    """Queries for all metadata attached to a given set of subjects, for a
    given type of metadata and indirected through the metadata package layer."""
    package_entries = relationship(subjects[0].__class__, 'package')
    package_meta_entries = relationship(lass.metadata.models.Package, meta_type)

    if package_entries is not None and package_meta_entries is not None:
        package_entry_model = relationship_to_model(package_entries)
        meta_model = relationship_to_model(package_meta_entries)

        query = lass.model_base.DBSession.query(
            lass.metadata.models.Key.name.label('key'),
            meta_model.value.label('value'),
            meta_model.effective_from.label('effective_from'),
            meta_model.effective_to.label('effective_to'),
            meta_model.subject_id.label('subject_id'),
            sqlalchemy.literal(priority).label('priority')
        ).select_from(
            meta_model
        ).join(
            package_entry_model.package,
            lass.metadata.models.Key
        ).filter(
            package_entry_model.subject_id.in_(
                [subject.id for subject in subjects]
            )
        )
    else:
        query = None
    return query


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


def search(term, keys, model, now=None):
    """Searches for the term 'term' in the metadata keys 'keys' of 'model'.

    Args:
        term: A string to search for; at time of writing, this will be searched
            for as a case-insensitive string fragment.
        keys: A list of names of metadata keys in which 'term' should be
            searched for.
        model: The model, whose textual metadata is in 'text_entries', whose
            metadata is to be searched and of which type the results should be.
        now: The time at which the metadata retrieved should be active.
            If None, the current time is used.  (Default: None.)

    Returns:
        A query returning a list of instances of 'model' for which one or more
        items of current metadata contain 'term'.
    """
    if now is None:
        now = lass.common.time.aware_now()
 
    # This is needed to force the backreferences on model that point to its
    # metadata to appear.  Any less hacky way of doing this is much appreciated.
    _ = model()

    meta = relationship_to_model(model.text_entries)

    return lass.model_base.DBSession.query(
        model
    ).join(
        model.text_entries
    ).filter(
        (meta.contains(now)) &
        (meta.value.ilike("%{}%".format(term))) &
        meta.key.has(lass.metadata.models.Key.name.in_(keys))
    ).order_by(
        meta.value
    )
