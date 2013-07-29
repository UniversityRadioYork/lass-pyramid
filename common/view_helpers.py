"""Functions for common view actions, such as lists.

---

Copyright (c) 2013, University Radio York.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import math
import pyramid
import sqlalchemy

import lass.model_base
import lass.metadata.models
import lass.metadata.query


def search(request, model, detail_route):
    """Implements a metadata search view for the given model.

    This view skeleton understands the following GET parameters:
        term: The search term to be used in the search.
        key: The name of a metadata key through which the search will occur.
            Multiple 'key's can be requested.
        search_type: Either 'All Results', which will yield a search results
            page, or 'First Result', which will go straight to the first result
            when one exists (similarly to Google(tm)'s I'm Feeling Lucky(tm)).
        page: See 'media_list'.

    Args:
        request: The request sent to the view calling this function.
        model: The model through whose metadata this search is searching.
        detail_route: The name of a route, taking a primary key belonging to an
            object in 'model', using which "more details" links may be
            constructed for the search results.

    Returns:
        A dictionary ready to be sent through 'view_config' that represents the
        view context for the search page renderer.
    """
    # Treat an empty term as a lack of term, and vice versa.
    term = request.params.get('term', '')
    keys = request.params.getall('keys')

    if term:
        results_list = media_list(
            request,
            lass.metadata.query.search(term, keys, model)
        )
    else:
        results_list = {}

    # Get the list of searchable keys for the search form.
    metadata_keys = (
        lass.model_base.DBSession.query(lass.metadata.models.Key).filter(
            lass.metadata.models.Key.searchable
        ).order_by(
            sqlalchemy.asc(lass.metadata.models.Key.plural)
        ).all()
    )

    return dict(
        {
            'term': term,
            'metadata_keys': metadata_keys
        },
        **results_list
    )


def media_list(request, all_items):
    """Implements a generic list view function.

    Given a SQLAlchemy query result and the request that triggered this view
    render, this function will return the appropriate view context dictionary
    for a list page.

    The view takes one GET parameter, 'page', which defaults to 1 and represents
    the page the user wishes to load, with 1 being the first page.  Any page
    requested outside the range 1-(maximum page needed to show 'items') will be
    clamped to the appropriate bound.

    Args:
        request: The request sent to the view calling this function.
        all_items: A query retrieving ALL items to display on this list IN ORDER
            OF DISPLAY.  (This will be sliced down to the correct range for the
            page itself.)

    Returns:
        A dictionary ready to be sent through 'view_config' that represents the
        view context for the list renderer.
    """
    items_per_page = 20

    count = all_items.count()
    if count:
        page = int(request.params.get('page', 1))
        page_total = math.ceil(all_items.count() / items_per_page)

        page = max(page, 1)
        page = min(page, page_total)

        items = all_items.slice(
            (page - 1) * items_per_page, page * items_per_page
        ).all()

        # If we can, we want to sprinkle metadata on the items.
        if items and hasattr(items[0].__class__, 'annotate'):
            items[0].__class__.annotate(items)
    else:
        page = 0
        page_total = 0
        items = []

    return {
        'items': items,
        'pages': page_total,
        'page': page
    }


def detail(request, id_name, source, target_name='item', constraint=None):
    """Implements a generic item detail view function.

    NOTE: At the moment, 'source' must have a column named 'id' to be matched
        against 'id_name'.  This should be replaced with an inspection
        to find the primary key at some point.

    Args:
        request: The request that triggered the calling view.
        id_name: The name of the matchdict key in which the primary key value of
            the item to retrieve can be found.
        source: The query that the ID should be retrieved from.  This allows
            constraints (such as 'has_showdb_entry' for shows) to be placed on IDs
            for which details can be found.
        target_name: The name to give to the template variable containing the
            item itself.  (Default: 'item'.)
        constraint: An optional function taking any matched item and returning
            True if it is allowed to have a detail page, and False otherwise.
            If not present, assume all items are allowed a detail page.
            (Default: None.)

    Returns:
        A dict suitable for returning from a rendered detail view.
    """
    if not constraint:
        constraint = lambda _: True

    item_id_str = request.matchdict[id_name]
    try:
        item_id = int(item_id_str)
    except ValueError:
        raise pyramid.exceptions.NotFound(
            'Invalid ID: {}.'.format(item_id_str)
        )

    item = source.get(item_id)
    if not (item and constraint(item)):
        raise pyramid.exceptions.NotFound(
            'Could not get details for any item with ID {}.'.format(
                item_id
            )
        )

    # Slap some metadata on the item, if possible.
    if hasattr(item.__class__, 'annotate'):
        item.__class__.annotate([item])

    return {
        'page_title': ((item.text['title']) + ['Untitled'])[0],
        target_name: item
    }
