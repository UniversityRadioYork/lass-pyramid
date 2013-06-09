"""Functions for selecting lists of timeslots based on certain criteria."""

import sqlalchemy
import datetime

from . import models


def next(count, start_at=None):
    """Selects the next 'count' shows, including the currently playing timeslot.

    Args:
        count: The maximum number of timeslots to select.
        start_at: The datetime used as a reference point to determine which
            shows are the 'next' ones.  (Default: now)

    Returns:
        A list of up to 'count' raw timeslots representing the next timeslots
        to occur from 'start_at' (or now if 'from' is None).
    """
    if not start_at:
        start_at = datetime.datetime.now(datetime.timezone.utc)

    return models.Timeslot.query.filter(
        ((models.Timeslot.start_time + models.Timeslot.duration) > start_at)
        & (models.ShowType.is_public == True)
    ).order_by(
        sqlalchemy.asc(models.Timeslot.start_time)
    ).limit(count).all()
