"""In which a mixin that allows attached metadata on a model to be
accessed in a common manner is described.

"""

import functools

from . import query


class MetadataSubject(object):
    """Mixin granting the ability to access metadata."""

    def meta_sources(self, meta_type):
        """
        Given a metadata type, returns an iterable of sources for that type.

        These are SQLAlchemy SELECT queries that return metadata, prioritised
        in order of appearance in the list.

        The list is *not* flattened out - use list concatenation or appending
        to include more lists.

        See 'metadata.query' for helper functions to construct sources.
        """
        return [
            query.own(self),
            query.default(self),
            query.package(self),
            query.default_package(self),
            # To add metadata inheritance, you would either add direct source
            # calls pointing to the parent object, OR append in a call to the
            # parent's 'meta_sources' using + or append.
        ]

    def meta(self, meta_type, *keys, date=None, sources=None, describe=False):
        """Returns the value(s) of the metadata under the given type and keys
        on the given date (or, if 'date' is None, the result of
        'self.meta_date').

        This function will try to use caching, first in the form of
        in-object cache and secondly by using any external cache set up.

        'sources', if undefined or falsy, will default to the value of
        'self.meta_sources'.

        'date', if undefined or falsy, will default to the value of
        'self.date'.
        """
        if not hasattr(self, '_meta_cache'):
            self._meta_cache = dict()

        hasher = functools.partial(
            query.cache_key,
            subject=self,
            meta_type=meta_type,
            date=date
        )
        hashes = {key: hasher(key=key) for key in keys}
        # Fetch in bulk any keys not already stored in the object cache.
        misses = [key for key in keys if hashes[key] not in self._meta_cache]
        if misses:
            results = query.run(
                self,
                meta_type,
                date if date else self.date,
                sources if sources else self.meta_sources(meta_type),
                *keys,
                describe=describe
            )
            self._meta_cache.update(
                {
                    hashes[key]: value
                    for key, value in results.items()
                }
            )
        return {key: self._meta_cache[hashes[key]] for key in keys}
