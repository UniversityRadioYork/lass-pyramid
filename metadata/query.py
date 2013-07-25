"""In which functions for composing and running metadata queries are found."""

import functools
import itertools
import hashlib
import sqlalchemy

import lass.common.rdbms
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

    return lass.common.rdbms.bulk_group(
        lass.model_base.DBSession.query(
            union.c.subject_id,
            union.c.key,
            union.c.value
        ).filter(
            (union.c.key.in_(keys)) &
            (lass.common.rdbms.transient_active_on(date, union))
        ).order_by(
            sqlalchemy.asc(union.c.subject_id),
            sqlalchemy.asc(union.c.key),
            sqlalchemy.asc(union.c.priority),
            sqlalchemy.desc(union.c.effective_from)
        )
    )
