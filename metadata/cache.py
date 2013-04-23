"""Interface to whichever cache backend the metadata system is using."""


def CacheMiss(Exception):
    """Exception raised when a cache miss occurs."""
    pass


def store(query, result):
    """Caches the result of the given query so that it can be re-fetched if the
    same query is run again,
    """
    pass


def retrieve(query):
    """Retrieves the query result from the cache, if it exists.

    Otherwise, 'CacheMiss' is raised.
    """
    raise CacheMiss
