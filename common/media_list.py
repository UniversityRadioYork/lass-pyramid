"""The innards of the 'media list' view helper, which implements a paginated
list given a SQLAlchemy ORM query.

The actual view helper is in 'lass.common.view_helpers'.

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


def page_number(request, page_total):
    """Gets the current page number of a media list.

    'request' is expected to have one query parameter, 'page',
    containing a page number (with the first page being page 1); if it
    does not exist, it is taken to be 1.  This page number may be
    outside the bounds dictated by 'page_total', but will be sanitised.

    Args:
        request: The request sent to the view calling this function.
        page_total: The total number of pages in the list, which must
            be non-negative.  If 0, the list is taken to be empty.

    Returns:
        The current page number, which will be 0 if 'page_total' is 0,
        or else will meet the bounds 1 <= page_number <= page_total.
    """
    if page_total < 0:
        raise ValueError('Page total was negative.')

    raw_page_number = int(request.params.get('page', 1))

    # Clamp the page number so it falls between 1 and the page total.
    # If the number of pages is zero, this will result in the page
    # number itself also being zero.  This is intentional and expected.
    page_number = min(max(raw_page_number, 1), page_total)

    assert (
        (0 < page_number) or (page_total == 0)
    ), 'Page number was zero when pages were available.'
    assert (
        (0 == page_number) or (1 <= page_number <= page_total)
    ), 'Page number was out of bounds.'

    return page_number


def page_total(source, items_per_page):
    """Calculates the total number of pages required for a media list.

    This function costs one database query per run.

    Args:
        source: An unevaluated SQLAlchemy ORM query representing the
            source of all items in this list, in the order in which
            they should appear in the list.
        items_per_page: The number of items that should appear on each
            page in the list.

    Returns:
        The page total, which will be a non-negative integer.
    """
    total = math.ceil(source.count() / items_per_page)

    assert 0 <= total, 'Page total was negative.'
    assert isinstance(total, int), 'Page total was not integral.'

    return total


def page_contents(source, items_per_page, page_number):
    """Retrieves the contents of a media list page.

    Args:
        source: An unevaluated SQLAlchemy ORM query representing the
            source of all items in this list, in the order in which
            they should appear in the list.
        items_per_page: The number of items that should appear on each
            page in the list.  The last page may have fewer items, but
            all other pages should be filled.
        page_number: The number of the page whose contents
            should be retrieved, or zero if there are no pages and thus
            no page contents.

    Returns:
        A list of objects from 'source' that together form the contents
        of the media list page numbered 'page_number', given that at
        most 'items_per_page' items appear on each page.  Each item
        will be annotated with the forms of metadata that will appear
        on the list.
    """
    if page_number < 0:
        raise ValueError('Page number was negative.')
    elif page_number == 0:
        items = []
    else:
        lower_bound = (page_number - 1) * items_per_page
        upper_bound = page_number * items_per_page
        items = source.slice(lower_bound, upper_bound).all()

        assert 0 < len(items), 'Empty page produced.'

        # If we can, we want to sprinkle metadata on the items.
        if hasattr(items[0].__class__, 'annotate'):
            items[0].__class__.annotate(items)

    return items
