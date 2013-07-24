"""In which functions for composing and running metadata queries are found."""

import functools
import hashlib
import sqlalchemy

import lass.common.rdbms
import lass.metadata.models


def get_attachment(model, attachment_type, meta_type):
    if not hasattr(model, attachment_type):
        setattr(model, attachment_type, {})
    attachment = getattr(model, attachment_type)

    if meta_type.name not in attachment:
        attachment[meta_type.name] = meta_type.attach(model)


def own(subjects, meta_type, priority):
    """Queries for all metadata attached to a given set of subjects, for a
    given type of metadata.""" 

    meta = sqlalchemy.inspection.inspect(
        getattr(subjects[0].__class__, meta_type + '_entries')
    ).mapper.class_

    return lass.model_base.DBSession.query(
        lass.metadata.models.Key.name.label('key'),
        meta.value.label('value'),
        meta.effective_from.label('effective_from'),
        meta.effective_to.label('effective_to'),
        meta.subject_id.label('subject_id'),
        sqlalchemy.literal(priority).label('priority')
    ).select_from(
        meta
    ).join(
        lass.metadata.models.Key
    ).filter(
        meta.subject_id.in_([subject.id for subject in subjects])
    )


def package(subjects, meta_type, priority):
    """Queries for all metadata attached to a given set of subjects, for a
    given type of metadata and indirected through the metadata package layer."""

    pkg_model = sqlalchemy.inspection.inspect(
        subjects[0].__class__.package_entries
    ).mapper.class_
    meta = sqlalchemy.inspection.inspect(
        getattr(subjects[0].__class__, meta_type + '_entries')
    ).mapper.class_

    return lass.model_base.DBSession.query(
        lass.metadata.models.Key.name.label('key'),
        meta.value.label('value'),
        meta.effective_from.label('effective_from'),
        meta.effective_to.label('effective_to'),
        meta.subject_id.label('subject_id'),
        sqlalchemy.literal(priority).label('priority')
    ).select_from(
        meta
    ).join(
        pkg_model.package,
        lass.metadata.models.Key
    ).filter(
        pkg_model.subject_id.in_([subject.id for subject in subjects])
    )


def run(subjects, meta_type, date, sources, *keys):
    # Metadata is currently held in a relational database.
    # It would be spiffing to change this
    first, *rest = (
        source(subjects, meta_type, priority)
        for priority, source in enumerate(sources)
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
