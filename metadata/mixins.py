"""In which a mixin that allows attached metadata on a model to be
accessed in a common manner is described.

"""

import collections
import datetime
import functools

from . import query


class MetadataSubject(object):
    """Mixin granting the ability to access metadata."""

    @classmethod
    def meta_sources(cls, meta_type):
        """
        Given a metadata type, returns an iterable of sources for that type.

        These are SQLAlchemy SELECT queries that return metadata, prioritised
        in order of appearance in the list.

        The list is *not* flattened out - use list concatenation or appending
        to include more lists.

        See 'metadata.query' for helper functions to construct sources.
        """
        return [
            query.own(with_default=True),
            query.package(with_default=True)
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
        sources=None,
        describe=False
    ):
        """Performs a metadata query on multiple objects of this class.

        Metadata is cached for the lifetime of this object.

        'sources', if undefined or falsy, will default to the value of
        'cls.meta_sources'.

        'date', if undefined or falsy, will default to the current time.
        """
        hits = collections.defaultdict(dict)
        misses = set()
        hashes = dict()
        for subject in subjects:
            hashes[subject], subject_hits, subject_misses = (
                subject.meta_cache_check(
                    meta_type,
                    date,
                    keys
                )
            )
            hits[subject.id].update(subject_hits)
            misses |= subject_misses
        if misses:
            results = query.run(
                subjects,
                meta_type,
                date if date else datetime.datetime.now(datetime.timezone.utc),
                sources if sources else cls.meta_sources(meta_type),
                *misses,
                describe=describe
            )
            for subject in subjects:
                hits[subject.id].update(results[subject.id])
                subject.meta_cache_update(hashes[subject], results[subject.id])

        return hits

    def meta_cache_update(self, hashes, results):
        self._meta_cache.update(
            {
                hashes[key]: value
                for key, value in results.items()
            }
        )

    def meta(self, *args, **keywords):
        """Performs a metadata query on this object only.

        See 'bulk_meta', for which this is a wrapper, for information on the
        arguments that may be passed to this.

        Example usage:
        show.meta('text', 'title') -> {'title': 'Slow Down Zone'}

        """
        return self.__class__.bulk_meta([self], *args, **keywords)[self.id]

    def meta_cache_check(self, meta_type, date, keys):
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
        hits, misses = dict(), set()
        for key in keys:
            h = hashes[key]
            if h in self._meta_cache:
                hits[key] = self._meta_cache[h]
            else:
                misses.add(key)
        return hashes, hits, misses
