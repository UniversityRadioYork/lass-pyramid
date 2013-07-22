import datetime
import functools
import pyramid
import sqlalchemy

import lass.model_base
import lass.schedule.models


@pyramid.view.view_config(
    route_name='schedule-shows',
    renderer='schedule/shows.jinja2'
)
def shows(request):
    """Displays a list of shows."""
    return lass.common.view_helpers.media_list(
        request,
        lass.schedule.models.Show.public(
        ).in_showdb(
        ).scheduled(
        ).order_by(
            sqlalchemy.desc(lass.schedule.models.Show.submitted_at)
        )
    )


@pyramid.view.view_config(
    route_name='schedule-show-detail',
    renderer='schedule/show_detail.jinja2'
)
def show_detail(request):
    """Displays detail about a show.

    This view expects the show's seasons to be listed, and thus these are
    eagerly loaded.
    """

    # Make sure the ID corresponds to a show that has a ShowDB entry.
    show_id = request.matchdict['showid']
    show = lass.schedule.models.Show.query.in_showdb().filter(
        lass.schedule.models.Show.id == show_id
    ).options(
        sqlalchemy.orm.joinedload(
            lass.schedule.models.Show.seasons,
            lass.schedule.models.Season.timeslots
        )
    ).first()
    if not show:
        raise pyramid.exceptions.NotFound(
            'Could not get details for any show with ID {}.'.format(
                show_id
            )
        )

    lass.schedule.models.Show.annotate([show])

    return {
        'show': show
    }
    
    
@pyramid.view.view_config(
    route_name='schedule-season-detail',
    renderer='schedule/season_detail.jinja2'
)
def season_detail(request):
    """Displays detail about a season.

    This view expects the season's timeslots to be listed, and thus these are
    eagerly loaded.
    """

    # Make sure the ID corresponds to a season that has a ShowDB entry.
    season_id = request.matchdict['seasonid']
    season = lass.schedule.models.Season.query.in_showdb().filter(
        lass.schedule.models.Season.id == season_id
    ).options(
        sqlalchemy.orm.joinedload(lass.schedule.models.Season.timeslots)
    ).first()
    if not season:
        raise pyramid.exceptions.NotFound(
            'Could not get details for any season with ID {}.'.format(
                season_id
            )
        )

    lass.schedule.models.Show.annotate([season.show])

    return {
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
        'timeslot': timeslot
    }


@pyramid.view.view_config(
    route_name='schedule'
)
def schedule(request):
    """The main schedule view.

    Currently this redirects to this week's schedule.
    """

    raise pyramid.exceptions.NotFound('TODO: implement this')


#
# DAY SCHEDULES
#


@pyramid.view.view_config(
    route_name='schedule-today',
    renderer='schedule/day.jinja2'
)
def today(request):
    """Shows the schedule for the current day (relative to local time)."""
    time_context = lass.common.time.context_from_config()
    return day(
        request,
        start_date=time_context.schedule_date_of(time_context.local_now()),
        time_context=time_context
    )


@pyramid.view.view_config(
    route_name='schedule-year-week-day',
    renderer='schedule/day.jinja2'
)
def year_week_day(request):
    """Shows the schedule for a specific day given in ISO Y/W/D format."""
    # Try to convert the incoming date information to Python representation
    try:
        start_date = lass.common.time.iso_to_gregorian(
            **{
                'iso_' + k: int(v)
                for k, v in request.matchdict.items()
                if k in ('year', 'week', 'day')
            }
        )
    except ValueError:
        raise pyramid.exceptions.NotFound(
            'Invalid date: {year}-W{week}-{day}'.format_map(
                request.matchdict
            )
        )

    time_context = lass.common.time.context_from_config()
    return day(request, start_date, time_context=time_context)


@pyramid.view.view_config(
    route_name='schedule-year-month-day',
    renderer='schedule/day.jinja2'
)
def year_month_day(request):
    """Shows the schedule for a specific day given in Y/M/D format."""
    # Try to convert the incoming date information to Python representation
    try:
        start_date = datetime.date(
            **{
                k: int(v)
                for k, v in request.matchdict.items()
                if k in ('year', 'month', 'day')
            }
        )
    except ValueError:
        raise pyramid.exceptions.NotFound(
            'Invalid date: {year}-{month}-{day}'.format_map(
                request.matchdict
            )
        )

    time_context = lass.common.time.context_from_config()
    return day(request, start_date, time_context=time_context)


#
# WEEK SCHEDULES
#

@pyramid.view.view_config(
    route_name='schedule-year-week',
    renderer='schedule/week.jinja2'
)
def year_week(request):
    """Shows the schedule for a specific week given in ISO Y/W format."""
    # Try to convert the incoming date information to Python representation
    try:
        start_date = lass.common.time.iso_to_gregorian(
            iso_day=1,
            **{
                'iso_' + k: int(v)
                for k, v in request.matchdict.items()
                if k in ('year', 'week')
            }
        )
    except ValueError:
        raise pyramid.exceptions.NotFound(
            'Invalid date: {year}-W{week}'.format_map(
                request.matchdict
            )
        )

    time_context = lass.common.time.context_from_config()
    return week(request, start_date, time_context=time_context)


def schedule_view(request, start_date, duration, time_context):
    """Common body for all full-schedule views."""

    # Make sure we start and finish at the start of programming, which
    # is a local time - this may mean some days are longer or shorter than
    # 24 hours due to DST, etc.
    start = time_context.start_on(start_date)
    finish = time_context.start_on(start_date + duration)
    true_duration = finish - start

    return {
        'start': start,
        'finish': finish,
        'duration': true_duration,
        'schedule': lass.schedule.lists.Schedule(
            creator=lass.schedule.lists.from_to,
            start=start,
            finish=finish
        )
    }


day = functools.partial(schedule_view, duration=datetime.timedelta(days=1))
week = functools.partial(schedule_view, duration=datetime.timedelta(weeks=1))


@pyramid.view.view_config(
    route_name='schedule-message',
    request_method='POST',
    request_param='comments'
)
def message(request):
    """
    Sends a message to the current show via the website.

    """
    # Current show
    timeslot = lass.schedule.lists.next(1)[0]

    # All redirects throw the user back at the index, with a query string set to
    # let the template know what the result of the message send was.
    # This should be extended eventually to allow redirects to a separate result
    # page for use when doing the message send via AJAX.  That, or throw actual
    # error/OK pages instead of redirects!
    redirect = lambda r: pyramid.httpexceptions.HTTPSeeOther(
        location=request.route_url(
            'index',
            _query={'msg_result': r}
        )
    )

    if not timeslot.can_be_messaged():
        raise redirect('no_msg')

    message = request.params['comments']

    message_config = lass.common.config.from_yaml('sitewide/message')
    message_l = message.lower()

    # Rudimentary spam check
    spam = message_config['spam']
    if any(x.lower() in message_l for x in spam):
        raise redirect('spam')

    # Social engineering filter
    warns = message_config['warns']
    message_parts = []
    for warn in warns:
        if any(x.lower() in message_l for x in warn['triggers']):
            message_parts.append(
                '<div class="ui-state-highlight"><span>{}</span></div>'.format(
                    warn['messages']
                )
            )
    message_parts.append(message)
    message = ''.join(message_parts.reverse())

    message_comm = lass.schedule.models.Message(
        commtypeid=3,  # Website communication
        sender='URY Website',
        timeslotid=timeslot.id,
        subject=message[:255],
        content=message,
        date=lass.common.time.aware_now(),
        statusid=1,  # Unread
        comm_source=request.client_addr
    )
    lass.DBSession.add(message_comm)
    lass.DBSession.commit()

    result = redirect('index')
    return result
