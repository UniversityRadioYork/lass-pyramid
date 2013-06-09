import pyramid
import yaml

import lass.model_base
import lass.schedule.lists
import lass.schedule.models

STATIC = 'assets:static'


class MockSchedule(object):
    @property
    def timeslots(self):
        if not hasattr(self, '_timeslots'):
            self._timeslots = lass.schedule.lists.next(10)
            lass.schedule.models.Timeslot.annotate(self._timeslots)
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
    website = {}

    a = pyramid.path.AssetResolver()
    with open(a.resolve('config:sitewide/website.yml').abspath()) as website_file:
        website.update(yaml.load(website_file))

    if 'pages' in website:
        website['pages'] = process_pages(request, website['pages'])

    return website


STREAMS = [
    {'quality': 'high', 'kbps': 192, 'url': 'live-high.m3u'},
    {'quality': 'low', 'kbps':  96, 'url': 'live-low.m3u'},
    {'quality': 'mobile', 'kbps':  48, 'url': 'live-mobile.m3u'}
]


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
    static = lambda *args: request.static_url('/'.join((STATIC,) + args))
    try:
        current_url = pyramid.url.current_route_url(request)
    except ValueError:
        current_url = None

    event.update(
        {
            'current_schedule': MockSchedule(),
            'transmitting': True,
            'website': website,
            'static': static,
            'url': request.route_url,
            'raw_url': lambda r: request.route_url('home') + r,
            'current_url': current_url,
            'page_title': get_page_title(request, current_url, website),
        }
    )


@pyramid.view.view_config(
    route_name='about',
    renderer='website/about.jinja2'
)
@pyramid.view.view_config(
    route_name='contact',
    renderer='website/contact.jinja2'
)
def static(request):
    """A view that can be used for static website pages.
    """
    return dict()


@pyramid.view.view_config(
    route_name='listen',
    renderer='website/listen.jinja2'
)
def listen(request):
    return {
        'streams': STREAMS
    }


@pyramid.view.view_config(
    route_name='home',
    renderer='website/index.jinja2'
)
def home(request):
    return {
        'page_title': 'Home'
    }


@pyramid.view.notfound_view_config(
    renderer='errors/404.jinja2',
    append_slash=True
)
def not_found(context, request):
    return {
        'page_title': 'Not Found'
    }
