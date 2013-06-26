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
    
    
@pyramid.view.view_config(
    route_name='schedule-season-detail',
    renderer='schedule/season_detail.jinja2'
)
def season_detail(request):
    """Displays detail about a season."""

    # Make sure the ID corresponds to a season that has a ShowDB entry.
    season_id = request.matchdict['seasonid']
    season = lass.schedule.models.Season.query.filter(
        lass.schedule.models.ShowType.has_showdb_entry,
        lass.schedule.models.Season.id == season_id
    ).first()
    if not season:
        raise pyramid.exceptions.NotFound(
            'Could not get details for any season with ID {}.'.format(
                season_id
            )
        )

    lass.schedule.models.Show.annotate([season.show])

    return {
        'page_title': ((season.show.text['title']) + ['Untitled'])[0],
        'season': season
    }


@pyramid.view.view_config(
    route_name='schedule-timeslot-detail',
    renderer='schedule/timeslot_detail.jinja2'
)
def timeslot_detail(request):
    """Displays detail about a timeslot."""

    # Make sure the ID corresponds to a timeslot that has a ShowDB entry.
    timeslot_id = request.matchdict['timeslotid']
    timeslot = lass.schedule.models.Timeslot.query.filter(
        lass.schedule.models.ShowType.has_showdb_entry,
        lass.schedule.models.Timeslot.id == timeslot_id
    ).first()
    if not timeslot:
        raise pyramid.exceptions.NotFound(
            'Could not get details for any timeslot with ID {}.'.format(
                timeslot_id
            )
        )

    lass.schedule.models.Timeslot.annotate([timeslot])

    return {
        'page_title': ((timeslot.text['title']) + ['Untitled'])[0],
        'timeslot': timeslot
    }
