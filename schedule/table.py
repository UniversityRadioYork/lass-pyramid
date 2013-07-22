"""The schedule tabulator."""

import datetime
import functools
import operator
import lass.common.time


###############################################################################
# Internal constants

# Common timedeltas
HOUR = datetime.timedelta(hours=1)
DAY = datetime.timedelta(days=1)


# The amount to add to the day number to get the schedule table column
# representing that day.
SCHEDULE_DAY_OFFSET = 1


# The column of the schedule table holding the time.
SCHEDULE_TIME_COL = 0


###############################################################################
# Public interface

def tabulate(start, slots, time_context=None):
    """Takes a list of slots and converts it into a week schedule table.

    Args:
        start: The aware datetime representing the start of the schedule.  May
            be any timezone.
        slots: The (filled, ordered, annotated) list of timeslots to tabulate.
            Should span one week, give or take differences due to DST.
        time_context: The context providing local date services.  May be None,
            in which case a new one is created.  (Default: None.)

    Returns:
        A list of schedule rows; each row is a dict consisting of 'time',
        'duration' and 'days', containing the start time (aware local, more
        specifically the start time on the first day), the duration as a
        timedelta, and a list of tuples of shows active during that row, and
        the number of rows they span respectively.
        Duplicated entries (those that carry on from the previous row) are
        marked with None.
    """
    if time_context is None:
        time_context = lass.common.time.context_from_config()

    local_week_start = time_context.localise(start)

    # Make up some utility functions
    shifter = time_context.shift_local
    day_after = functools.partial(shifter, delta=DAY)
    start_of = lambda slot: time_context.localise(slot.start)
    finish_of = lambda slot: time_context.localise(slot.finish)

    days, partitions = split_days(
        local_week_start,
        slots,
        day_after,
        start_of,
        finish_of
    )
    table = empty_table(local_week_start, partitions, len(days))
    populate_table(table, days, finish_of, shifter)
    return [
        {'start': time, 'days': days}
        for time, *days in table
    ]


###############################################################################
# Internals

# 1. Day splitting and partitioning #

def split_days(start, slots, day_after, start_of, finish_of):
    """Takes a list of slots and splits it into many lists of one day each.

    This function also creates a set of times representing the starts of
    timeslots across the day lists, as local-time deltas between the schedule
    start and the timeslot start.  This is useful for dividing the schedule
    into rows later.

    Args:
        start: The aware local datetime representing the schedule start.
        slots: The schedule data, as a fully filled list of timeslots spanning
            the schedule's full range and starting at the schedule's designated
            start.
        day_after: A function taking one aware local datetime and shifting it
            by one day, taking into account DST and other timezone changes.
        start_of: A function taking a timeslot and returning its start
            as a local aware datetime.
        finish_of: A function taking a timeslot and returning its finish
            as a local aware datetime.

    Returns:
        a tuple containing the result of splitting the data into day lists, and
        the set of observed show start times for dividing the schedule up into
        rows later
    """
    done_day_lists = []
    day_list = []
    partitions = set([])

    day_start = start
    day_finish = day_after(day_start)

    for slot in slots:
        slot_start = start_of(slot)
        slot_finish = finish_of(slot)
        # If the next slot is outside the day we're looking at. advance it.
        # To deal with shows straddling multiple days, check for multiple
        # rotations (hence the while loop).
        while day_finish <= slot_start:
            day_list = advance_day(
                day_finish,
                day_list,
                done_day_lists,
                finish_of
            )
            day_start, day_finish = day_finish, day_after(day_finish)

        day_list.append(slot)

        if not slot.is_collapsible:
            add_partitions(
                partitions,
                day_start,
                day_finish,
                slot_start,
                slot_finish
            )

    # Finish off by pushing the last day onto the list, as nothing else will
    done_day_lists.append(day_list)
    return done_day_lists, partitions


def add_partitions(partitions, day_start, day_finish, slot_start, slot_finish):
    """Add row boundaries arising from this slot to the partition list.

    Whether or not the timeslot emits row boundaries depends on its type;
    generally filler slots will not emit full row boundaries, causing the
    schedule to 'fold up' where no shows are scheduled at that time for an
    entire week.

    Args:
        partitions: The set of partitions that may be modified by this
            function.
        day_start: The aware local datetime at which the day currently being
            split begins.
        day_finish: The aware local datetime of the day's end.
        slot_start: The aware local datetime at which the current timeslot
            begins.
        slot_finish: The aware local datetime of the slot's end.
    """
    # Prevent negative partitions if the show started on a previous day.
    start_p = max(day_start, slot_start) - day_start
    # And overly large ones if the show ends on another day.
    end_p = min(day_finish, slot_finish) - day_start

    partitions |= {start_p, end_p}

    # Now add all the exact hours between start_p and end_p, if any
    # (hour_p is set to the next hour after start_p)
    hour_p = datetime.timedelta(
        days=start_p.days,
        seconds=(
            start_p.seconds - (start_p.seconds % (60 * 60))
        ) + (60 * 60)
    )
    while hour_p < end_p:
        partitions.add(hour_p)
        hour_p += HOUR


def advance_day(day_finish, day_list, done_day_lists, finish_of):
    """Ends the current day and sets things up ready to process the next day.

    Args:
        day_finish: The aware local datetime of the end of the day that is about
            to finish (and, thus, also the start of the next day)
        day_list: The completed list of timeslots for the day being finished.
        done_day_lists: the list of completed day lists (in chronological
            order) to push the new day onto
        finish_of: A function taking a timeslot and returning its finish
            as a local aware datetime.
    Returns:
        The initial list for the new day, which may or may not be empty
        depending on show day crossover.
    """
    # We should NEVER be storing an empty list, as every day should at least
    # have one show (the filler show).
    if not day_list:
        raise ValueError(
            'split_days encountered empty day list, is filler working? '
            '(day_finish={} day_list={} done_day_lists={})'.format(
                day_finish,
                day_list,
                done_day_lists
            )
        )

    done_day_lists.append(day_list)

    # We need to see if the last show we processed straddles the boundary
    # between the two days and, if so, make sure it appears at the start of the
    # new list too.
    last_show = day_list[-1]
    return [last_show] if finish_of(last_show) > day_finish else []


# 2. Empty table generation #

def empty_table(start, partitions, n_cols):
    """Creates an empty schedule table.

    Args:
        start: The (active local) schedule start datetime.
        partitions: The set of row starts, as offsets from nlstart.
        n_cols: The number of schedule columns (days), usually 7.

    Returns:
        An empty schedule table ready for population with show data,
        implemented as a list of row lists.
        The table will contain len(partitions) rows, each containing the 
        time of their occurrence (on the first day of the schedule; add day
        offsets for the other days), then num_cols instances of None ready to
        be filled with schedule data.
    """
    # We don't want the last partition, as it marks the end of the day.
    return [[(start + i)] + ([None] * n_cols) for i in sorted(partitions)][:-1]


# 3. Population #

def populate_table(table, data_lists, finish_of, shifter):
    """Populates empty schedule tables with data from the given lists.

    Args:
        table: the empty table (generally created by empty_table) to populate
            with schedule data; this is potentially mutated in-place.
        data_lists: a list of lists, each representing one day of consecutive
            timeslots.
        finish_of: A function taking a timeslot and returning its finish
            as a local aware datetime.

    Returns:
        the populated table, which may or may not be the same object as table
        depending on implementation.
    """
    for i, day in enumerate(data_lists):
        populate_table_day(
            make_row_date(table, i, shifter),
            make_add_to_table(table, i),
            finish_of,
            day
        )
    return table


def populate_table_day(row_date, add_to_table, finish_of, day):
    """Adds a day of slots into the table using the given functions.

    Args:
        row_date: A function taking a table row index and returning the naive
            local datetime of its start on this day.
        add_to_table: A function taking a table row index, a timeslot whose
            record starting on that row and the number of rows it spans, and
            adding it into the schedule table.
        finish_of: A function taking a timeslot and returning its finish
            as a local aware datetime.
        day: The day to add into the table.
    """
    current_row = 0
    for slot in day:
        start_row = current_row
        hit_bottom = False

        # How much local time does this slot take up?
        finish = finish_of(slot)

        # Work out how many rows this slot fits into.
        try:
            while row_date(current_row) < finish:
                current_row += 1
        except IndexError:
            # This usually means this show crosses over the day boundary;
            # this is normal.
            hit_bottom = True
        else:

            # If our partitioning is sound and we haven't run off the end
            # of a day, then the slot must fit exactly into one or more
            # rows.
            if not hit_bottom and row_date(current_row) > finish:
                raise ValueError(
                    'Partitioning unsound - show exceeds partition bounds.'
                    ' (Row {}, show {}, date {} > {} < {})'.format(
                        current_row,
                        slot,
                        row_date(current_row),
                        finish,
                        row_date(current_row + 1)
                    )
                )

        add_to_table(start_row, slot, current_row - start_row)


###############################################################################
# Higher-order functions

def make_row_date(table, days, shifter):
    """A function that makes a function mapping rows to their starting
    datetimes.

    Args:
        table: The schedule table the returned function will look-up dates in.
        days: The number of days since the start of the schedule.
        shifter: A function taking a datetime and timedelta, and shifting the
            former by the latter taking into account DST and suchlike.

    Returns:
        A function closed over table and day_offset that takes a row and
        returns its datetime for the day being considered.
    """
    return lambda row: shifter(
        table[row][SCHEDULE_TIME_COL],
        delta=datetime.timedelta(days=days)
    )


def make_add_to_table(table, days):
    """A function that makes a function that adds a slot into a table.

    Args:
        table: the schedule table the returned function will add entries into.
        days: the number of days since the start of the schedule.

    Returns:
        a function closed over table and day_offset that takes a row, timeslot
        to place on that row and that timeslot's row occupacy, and inserts the
        data into the schedule table.
    """
    col = SCHEDULE_DAY_OFFSET + days
    return (
        lambda row, slot, rows:
        None if rows == 0 else operator.setitem(table[row], col, (slot, rows))
    )
