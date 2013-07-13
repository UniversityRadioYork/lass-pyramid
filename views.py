import datetime
import pyramid

import lass.common.config
import lass.common.time
import lass.model_base
import lass.schedule.filler
import lass.schedule.lists
import lass.schedule.models

STATIC = 'assets:static'


class MockSchedule(object):
    @property
    def timeslots(self):
        if not hasattr(self, '_timeslots'):
            self._timeslots = lass.schedule.lists.next(10)
        return self._timeslots


def process_pages(request, pages):
    new_pages = {}
    for name, page in pages.items():
        target = page['target']

        new_page = page

        # Expand out route-based targets.
        if target.startswith('~'):
            new_page['target'] = request.route_url(target[1:])

        new_pages[name] = new_page
    return new_pages


def make_website(request):
    website = lass.common.config.from_yaml('sitewide/website')


    if 'pages' in website:
        website['pages'] = process_pages(request, website['pages'])

    return website


def get_page_title(request, current_url, website):
    """Looks up the page title corresponding to the request's view name."""
    page_title = 'Untitled'
    for pt, page in website['pages'].items():
        if current_url == page['target']:
            page_title = pt
            break
    return page_title


@pyramid.events.subscriber(pyramid.events.BeforeRender)
def standard_context(event):
    request = event['request']

    website = make_website(request)
    try:
        current_url = pyramid.url.current_route_url(request)
    except ValueError:
        current_url = None

    event.update(
        {
            'now': lass.common.time.aware_now(),
            'date_config': lass.common.time.load_date_config(),

            'current_schedule': MockSchedule(),
            'transmitting': True,
            'broadcasting': True,
            'website': website,
            'raw_url': lambda r: request.route_url('home') + r,
            'current_url': current_url,
            'page_title': get_page_title(request, current_url, website),
        }
    )
