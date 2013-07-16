import pyramid

import lass.common.config
import lass.common.time
import lass.model_base
import lass.schedule.filler
import lass.schedule.lists
import lass.schedule.models

STATIC = 'assets:static'


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
    else:
        title = 'Not Found'

    return dict(page, title=title)


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
            'date_config': lass.common.time.load_date_config(),

            'current_schedule': lass.schedule.lists.Lazy(
                lambda: lass.schedule.lists.next(10)
            ),
            'service_state': lass.schedule.service.State(),
            'website': website,
            'raw_url': lambda r: request.route_url('home') + r,
            'current_url': current_url,
            'this_page': get_page(request, current_url, website)
        }
    )
