"""The filler module provides functions for manipulating and
inserting filler slots.

Filler slots are fake timeslots, tied to a fake season (which is
assigned to a real show), that are optionally used to pad out gaps
in timeslot ranges.

This allows functions further up the chain to work with the
assumption that timeslot ranges are contiguous (that is, there are
no gaps between one timeslot's end and another timeslot's start).

Branding filler shows
=====================

At the time of writing, the filler slots correspond to URY Jukebox
programming, but the filler show is stored in the show database
as an actual show and thus the branding of the filler programming may
vary via the show metadata system.

Defining the filler show
========================

The filler show must exist in the database as the only show with the
show type named 'filler'.

.. WARNING:
   This show type obviously must also exist.
"""

import datetime
import functools

import lass.common.config
import lass.schedule.models


class FillerTimeslot(lass.schedule.models.BaseTimeslot):
    """An object representing a filler timeslot.
    
    Filler timeslots are mostly compatible with regular timeslots, but their
    start and duration are always None, and their """
    def __init__(self, start_time, duration, metadata=None):
        super().__init__(start_time, duration)
        for attr, contents in metadata.items():
            setattr(self, attr, contents)


def filler_from_config():
    """Creates a filler function that creates fake filler timeslots with
    metadata taken from the website's configuration files (specifically
    'sitewide/filler.yml'.
    """
    filler_config = lass.common.config.from_yaml('sitewide/filler')
    return functools.partial(
        FillerTimeslot,
        metadata=filler_config['metadata']
    )


## FILLING ALGORITHM

ZERO = datetime.timedelta(seconds=0)
def fill(timeslots, filler, start_time, end_time):
    """Fills any gaps in the given timeslot list with filler slots,
    such that the list is fully populated from the given start time
    to the given end time.

    Args:
        timeslots: The list of timeslots, may be empty.
        start_time: the start date/time.
        end_time: the end date/time.
    """
    if start_time > end_time:
        raise ValueError('Start time is after end time.')

    current_time = start_time
    filled = []
    unplaced = iter(timeslots)

    while current_time < end_time:
        timeslot = next(unplaced, None)
        end = min(end_time, timeslot.start_time) if timeslot else end_time
        gap = end - current_time

        if gap < ZERO:
            raise ValueError('Negative gap.')
        elif gap > ZERO:
            filled.append(filler(current_time, gap))
            current_time += gap
        # If no gap, don't fill!

        if timeslot:
            filled.append(timeslot)
            current_time += timeslot.duration

    return filled
