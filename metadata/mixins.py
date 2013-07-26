"""In which a mixin that allows attached metadata on a model to be
accessed in a common manner is described.

"""

import collections
import datetime
import functools

import lass.model_base
import lass.common.time
import lass.common.utils
import lass.metadata.query
import lass.people.mixins


class MetadataSubject(object):
    """Mixin granting the ability to access metadata."""

    @classmethod
    def add_meta(cls, items, meta_type, *keys, date=None, attr=None):
        """Annotates a set of items with their metadata.

        This is a bulk metadata query operation (one metadata query per call).

        Args:
            items: The items to annotate.  These MUST be instances of 'cls'. 
            meta_type: The metadata type to fetch from, for example 'text' or
                'image'.
            *keys: The metadata key names to fetch metadata for.  If no keys are
                provided, all metadata keys are returned.
            date: The date (as a datetime) on which the retrieved metadata should be
                active. (Default: see 'bulk_meta')
            attr: The name of the attribute on the items in which the metadata
                dictionary will be stored.  (Default: the value of meta_type)
        """
        if items:
            lass.common.utils.annotate(
                items,
                cls.bulk_meta(items, meta_type, *keys, date=date),
                attribute_name=attr if attr else meta_type
            )

    @classmethod
    def meta_sources(cls):
        """
        Given a metadata type, returns an iterable of sources for that type.

        These are SQLAlchemy SELECT queries that return metadata, prioritised
        in order of appearance in the list.

        The list is *not* flattened out - use list concatenation or appending
        to include more lists.

        See 'metadata.query' for helper functions to construct sources.
        """
        return [
            lass.metadata.query.own,
            lass.metadata.query.package
            # To add metadata inheritance, you would either add direct source
            # calls pointing to the parent object, OR append in a call to the
            # parent's 'meta_sources' using + or append.
        ]

    @classmethod
    def bulk_meta(
        cls,
        subjects,
        meta_type,
        *keys,
        date=None,
        sources=None
    ):
        """Performs a metadata query on multiple objects of this class.

        Metadata is cached for the lifetime of this object.

        'sources', if undefined or falsy, will default to the value of
        'cls.meta_sources'.

        'date', if undefined or falsy, will default to the current time.
        """
        return lass.metadata.query.run(
            subjects,
            meta_type,
            date if date else lass.common.time.aware_now(),
            sources if sources else cls.meta_sources(),
            *keys
        )
