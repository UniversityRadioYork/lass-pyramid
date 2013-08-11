import functools
import operator
import pyramid
import sqlalchemy

import lass.common.config
import lass.common.time
import lass.model_base
import lass.schedule.filler
import lass.schedule.lists
import lass.schedule.models


def get_page(request, current_url, website):
    """Looks up the current page and its title in the page configuration."""
    page = {}
    title = 'Untitled'

    if request.matched_route:
        rname = request.matched_route.name
        try:
            title, page = next(
                (t, p) for t, p in website['pages'].items()
                if rname == p.get('route')
            )
        except StopIteration:
            # Yield the default page/title above
            pass

    return dict(page, title=title)


def get_streams(website):
    """Returns a list of all streams on the website.

    Args:
        website: The main website configuration dictionary.

    Returns:
        A list of dictionaries with keys 'name', 'mount', 'format' and
        'kbps', ordered in descending quality (kbps).
    """
    return sorted(
        (
            dict(value, name=key)
            for key, value in website['streams'].items()
        ),
        key=operator.itemgetter('kbps'),
        reverse=True
    )


@pyramid.events.subscriber(pyramid.events.BeforeRender)
def standard_context(event):
    request = event['request']

    website = lass.common.config.from_yaml('sitewide/website')

    try:
        current_url = pyramid.url.current_route_url(request)
    except ValueError:
        current_url = None

    event.update(
        {
            'now': lass.common.time.aware_now(),
            'date_config': lass.common.time.context_from_config(),

            'current_schedule': lass.schedule.lists.Schedule(
                functools.partial(lass.schedule.lists.next, count=10)
            ),
            'service_state': lass.schedule.service.State(),
            'website': website,
            'raw_url': lambda r: request.route_url('home') + r,
            'current_url': current_url,
            'this_page': get_page(request, current_url, website),
            'streams': get_streams(website)
        }
    )


@pyramid.view.view_config(
    context=sqlalchemy.exc.OperationalError,
    renderer='errors/database.jinja2'
)
def database_oops(exc, _):
    """View triggered when the database falls over."""
    return {
        'no_database': True,
        'exception': exc
    }
