import math

import pyramid
import sqlalchemy

import lass.model_base
import lass.schedule.models


# Configure this at some point
SHOWS_PER_PAGE = 25
@pyramid.view.view_config(
    route_name='schedule-shows',
    renderer='schedule/shows.jinja2'
)
def show_list(request):
    """Displays a list of shows."""
    all_shows = lass.schedule.models.Show.query.public(
    ).in_showdb(
    ).scheduled(
    ).order_by(
        sqlalchemy.desc(lass.schedule.models.Show.submitted_at)
    )
    page = int(request.params.get('page', 1))
    show_page_count = math.ceil(all_shows.count() / SHOWS_PER_PAGE)

    page = max(page, 1)
    page = min(page, show_page_count)

    shows = all_shows.slice(
        (page - 1) * SHOWS_PER_PAGE, page * SHOWS_PER_PAGE
    ).all()

    lass.schedule.models.Show.annotate(shows)

    return {
        'shows': shows,
        'pages': show_page_count,
        'page': page,
    }


@pyramid.view.view_config(
    route_name='schedule-show-detail',
    renderer='schedule/show_detail.jinja2'
)
def show_detail(request):
    """Displays detail about a show."""

    # Make sure the ID corresponds to a show that has a ShowDB entry.
    show_id = request.matchdict['showid']
    show = lass.schedule.models.Show.query.in_showdb(
    ).filter(
        lass.schedule.models.Show.id == show_id
    ).first()
    if not show:
        raise pyramid.exceptions.NotFound(
            'Could not get details for any show with ID {}.'.format(
                show_id
            )
        )

    lass.schedule.models.Show.annotate([show])

    return {
        'page_title': ((show.text['title']) + ['Untitled'])[0],
        'show': show
    }
