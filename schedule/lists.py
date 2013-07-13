"""Functions for selecting lists of timeslots based on certain criteria."""

import datetime
import sqlalchemy

from . import models

import lass.common.time
import lass.schedule.filler


class Lazy(object):
    """Lazy loader/cache for schedule lists."""
    def __init__(self, function):
        """Initialises the lazy loader.

        Args:
            function: A zero-arguments lambda/thunk to evaluate to retrieve
            the schedule data.  Usually should be of the form
            "lambda: f(foo, bar, baz)".

        Returns:
            A Lazy object.
        """
        self.function = function
        self.stored = False
        self.contents = None

    @property
    def timeslots(self):
        """Retrieves the list of timeslots this Lazy object is set to retrieve.

        If the timeslots have not yet been retrieved, this will invoke the
        retrieval function and then save the results for future calls on this
        object only.

        Returns:
            The list of timeslots this Lazy object has been directed to compute.
        """
        if not self.stored:
            self.contents = self.function()
            self.stored = True

        return self.contents


def next(count, start_at=None):
    """Selects the next 'count' shows, including the currently playing timeslot,
    and performs filling and annotating.

    Args:
        count: The maximum number of timeslots to select.
        start_at: The datetime used as a reference point to determine which
            shows are the 'next' ones.  (Default: now)

    Returns:
        A list containing up to 'count' timeslots, which may either be actual
        timeslots or filler.  The list represents the next 'count' timeslots
        to occur from 'start_at', with any trailing filler limited to at most
        one day in length.
    """
    if not start_at:
        start_at = lass.common.time.aware_now()

    raw = lass.schedule.lists.next_raw(count, start_at)
    if raw:
        lass.schedule.models.Timeslot.annotate(raw)
        start = min(raw[0].start_time, start_at)
        end = raw[-1].end_time
    else:
        start = start_at
        end = start_at

    return lass.schedule.filler.fill(
        raw,
        lass.schedule.filler.filler_from_config(),
        start_time=start,
        end_time=end + datetime.timedelta(hours=24)
    )[:count]


def next_raw(count, start_at=None):
    """Selects the next 'count' shows, including the currently playing timeslot.

    No filling is done.

    Args:
        count: The maximum number of timeslots to select.
        start_at: The datetime used as a reference point to determine which
            shows are the 'next' ones.  (Default: now)

    Returns:
        A list of up to 'count' raw timeslots representing the next timeslots
        to occur from 'start_at' (or now if 'from' is None).
    """
    if not start_at:
        start_at = lass.common.time.aware_now

    return models.Timeslot.query.filter(
        ((models.Timeslot.start_time + models.Timeslot.duration) > start_at)
        & (models.ShowType.is_public == True)
    ).order_by(
        sqlalchemy.asc(models.Timeslot.start_time)
    ).limit(count).all()
