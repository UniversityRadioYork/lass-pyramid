"""Functions for dealing with credits inside queries.

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
import sqlalchemy


def add_to_query(query, through=('credits',)):
    """Given a query on a model, load credits into that query.

    This produces an options() call, and thus can be called whenever one
    would be appropriate for the target query.

    This function is fail-safe in that if it is passed a model that does
    not use database credits directly, it does nothing.

    Args:
        query: A SQLAlchemy query on that can have an eager load
            options block added to it.  To work, this function must be
            able to load through the path given by 'through'.
        through: The relationship path that should be used to find the
            credits.  By default, this just looks directly for a
            relationship called 'credits'.  (Default: ('credits',))


    Returns:
        The new query object with credits being eagerly loaded in.
    """
    try:
        new_query = query.options(sqlalchemy.orm.subqueryload(*through))
    except AttributeError:
        # Couldn't find 'credits' at all
        new_query = query
    except sqlalchemy.exc.ArgumentError:
        # Could find 'credits', but it wasn't a relationship
        new_query = query

    return new_query
