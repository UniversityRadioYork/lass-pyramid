"""Functions for selecting lists of timeslots based on certain criteria."""

import datetime
import functools
import sqlalchemy

import lass.schedule.models

import lass.common.time
import lass.schedule.filler


def process(slots, start, finish):
    """Processes a raw list of timeslots, annotating and filling them.

    Args:
        slots: The list of timeslots.  May be mutated.
        start: The datetime representing the desired start of the schedule;
            filler will pad between here and the first timeslot, if necessary.
        finish: The datetime representing the desired end of the schedule;
            filler will pad between the last timeslot and here, if necessary.

    Returns:
        The list 'slots', augmented with filler and metadata/credits
        annotations.  The list may exceed the boundaries of
        'start' and 'finish', but should be filled to meet them at least.
    """
    if slots:
        lass.schedule.models.Timeslot.annotate(slots)
        start = min(slots[0].start, start)
        finish = max(slots[-1].finish, finish)

    return lass.schedule.filler.fill(
        slots,
        lass.schedule.filler.filler_from_config(),
        start,
        finish
    )


class Schedule(object):
    """Lazy loader/cache for schedule lists."""
    def __init__(
        self,
        creator,
        processor=process,
        source=None,
        start=None,
        finish=None
    ):
        """Initialises the lazy loader.

        Args:
            creator: A function taking the start time and returning a list of
                unfilled and unannotated timeslots.
            processor: A processing function for post-processing the output of
                'function' (for example, annotating and filling).  (Default:
                'process'.)
            source: A Query from which all timeslots should be selected.
                May be None, in which case the query matching all public
                timeslots will be used.
                (Default: None.)
            start: The datetime at which the schedule should start.
                May be None, in which case the date/time at calling is used.
                (Default: None.)
            finish: The datetime at which the schedule should finish.
                May be None, in which case the schedule finishes one day after
                it starts.
                (Default: None.)

        Returns:
            A Schedule object.
        """
        self.slots = None
        self.source = lass.schedule.models.Timeslot.query.public()

        self.start = start if start else lass.common.time.aware_now()
        self.finish = finish if finish else (
            self.start + datetime.timedelta(days=1)
        )

        self.creator = functools.partial(
            creator,
            source=self.source,
            start=self.start,
            finish=self.finish
        )
        self.processor = functools.partial(
            processor,
            start=self.start,
            finish=self.finish
        )
        self.stored = False

    @property
    def timeslots(self):
        """Retrieves the list of timeslots this Schedule object is set to
        retrieve.

        If the timeslots have not yet been retrieved, this will invoke the
        retrieval function and then save the results for future calls on this
        object only.

        Returns:
            The list of timeslots this object has been directed to compute.
        """
        if not self.stored:
            self.slots = self.processor(self.creator())
            self.stored = True

        return self.slots


def from_to(source, start, finish):
    """Selects all shows between 'start' and 'finish'.

    No filling is done, and shows selected may start or finish outside the
    boundaries required; consequently the start of the first and end of the
    last show may not equate to start and finish respectively.

    Args:
        source: A query providing the timeslots from which this function should
            select.  For all public shows, use 'Timeslot.query.public()',
            for example.
        start: The datetime representing the start of the schedule.
        finish: The datetime representing the finish of the schedule.

    Returns:
        A raw ordered list of every show from 'source' with air-time between
        'start' and 'finish'.
    """
    return source.filter(
        (lass.schedule.models.Timeslot.start <= finish) &
        (
            (
                lass.schedule.models.Timeslot.start +
                lass.schedule.models.Timeslot.duration
            ) > start
        )
    ).order_by(
        sqlalchemy.asc(lass.schedule.models.Timeslot.start)
    ).all()


def next(source, start, finish, count):
    """Selects the next 'count' shows, including the currently playing timeslot.

    No filling is done.

    Args:
        source: A query providing the timeslots from which this function should
            select.  For all public shows, use 'Timeslot.query.public()',
            for example.
        count: The maximum number of timeslots to select.
        start: The datetime used as a reference point to determine which
            shows are the 'next' ones.  (Default: now)
        finish: Ignored; kept for interface consistency.


    Returns:
        A list of up to 'count' raw timeslots representing the next timeslots
        to occur from 'start' (or now if 'from' is None).
    """
    return source.filter(
        (
            lass.schedule.models.Timeslot.start +
            lass.schedule.models.Timeslot.duration
        ) > start
    ).order_by(
        sqlalchemy.asc(lass.schedule.models.Timeslot.start)
    ).limit(count).all()
