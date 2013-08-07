"""Functions for dealing with schedule blocks.

---

Copyright (c) 2013, University Radio York.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import datetime
import fnmatch
import functools
import itertools

import lass.common.config
import lass.common.time


def annotate(timeslots):
    """Annotates timeslots with their schedule blocks.

    Each timeslot is augmented with a new attribute 'block' that points either
    to None (in the case of the timeslot having no attached block) or a dict
    with keys 'name' and 'type' denoting the block's descriptive name and
    internal type key, respectively.

    Args:
        timeslots: A list of timeslots to be annotated as described above.  The
            timeslots must be sorted in chronological order with respect to
            start time.

    Returns:
        Nothing; the timeslots are modified in-place.
    """
    conf = block_config()
    time_context = lass.common.time.context_from_config()

    if timeslots:
        start_date = time_context.schedule_date_of(timeslots[0].start)
        range_blocks = range_iter(
            conf['range_blocks'],
            start_date,
            time_context
        )
        next_range_block = make_next_range_block_function(range_blocks)

        for timeslot in timeslots:
            range_block, next_range_block = next_range_block(timeslot)
            name_block = name_block_for_timeslot(timeslot, conf)

            # Name blocks take precedence if available.
            block_name = name_block if name_block is not None else range_block
            timeslot.block = (
                None
                if block_name is None
                else dict(conf['blocks'][block_name], name=block_name)
            )


def range_iter(blocks, start_date, time_context):
    """Produces an iterator that returns range blocks in succession.

    The iterator will produce 2-tuples of the form (active datetime,
    block name) where the latter may be None (signifying the absence of
    active range-block). The former starts at the first block on
    start_date and continues forwards on each block change point, the
    date advancing by one day each time the block list is exhausted and
    restarted.

    Args:
        blocks: An iterable consisting of 3-tuples (or equivalents) of
        the form (hour, minute, name), in ascending chronological order
        from midnight and with hour and minute representing a local time
        at which the block referred to by 'name' is to be active.

    Returns:
        An "infinite" iterable (actually bounded by the maximum allowed
        date!) that will provide the above tuples.
    """
    date = start_date
    while True:
        yield from (
            (
                time_context.combine_as_local(
                    date,
                    datetime.time(hour=int(h), minute=int(m), second=0)
                ), name
            ) for (h, m, name) in blocks
        )
        date += datetime.timedelta(days=1)


def block_config():
    """Retrieves the default block configuration."""
    return lass.common.config.from_yaml('sitewide/blocks')


def name_block_for_timeslot(timeslot, block_config):
    """Retrieves the name-based block match for this timeslot, if any.

    If multiple matches are found, the first is retrieved, even if it
    is an exclusion match (block is None).

    Args:
        timeslot: The timeslot whose first name block match should be
            returned.
        block_config: The block configuration that defines the name
            blocks.

    Returns:
        Either None, signifying that this timeslot has no name block,
        or otherwise the name of the name block in which this timeslot
        resides.
    """
    return next(
        (
            block for pattern, block in block_config['name_blocks']
            if name_block_match(timeslot, pattern)
        ),
        None
    )


def name_block_match(timeslot, pattern):
    """Returns True if the timeslot matches the name block pattern."""
    match = False

    if hasattr(timeslot, 'text'):
        title = timeslot.text.get('title', [''])[0]
        # Match case insensitively
        match = fnmatch.fnmatch(title.lower(), pattern.lower())

    return match


def make_next_range_block_function(iterator):
    """Makes a function that takes a timeslot and gets its range block.

    The function returned here is a slightly strange function, in that
    it returns not only the range block for a timeslot but another
    function, which will return the range block for the next timeslot.
    This is because each function records the block that was active in
    the last timeslot, as well as the next block.

    Args:
        iterator: The iterator (from 'range_iter', usually) that will
            supply the range blocks.  This should not be used outside of
            the returned function.

    Returns:
        A function that takes in a timeslot and returns a tuple
        (timeslot block name, next function).  The function should not
        be called again and should be replaced with the next function.
        See the inline definition of 'f' below for details.

    """
    def f(this_start, this_name, next_start, next_name, timeslot):
        """Returns the range block a timeslot exists within.

        This function will advance the range block iterator.

        Args:
            timeslot: The timeslot whose range block should be given.
                All timeslots must be presented in ascending
                chronological order.
            this_start: The start time of the block 'this_name'.
            this_name: The name of the block that was active during the
                last timeslot.
            next_start: The time at which 'next' becomes active.
            next_name: The name of the next block to become active.

        Returns:
            A tuple whose first item is the range block active at the
            start of 'timeslot' and whose second is the function to use
            to retrieve the next timeslot's block.
        """
        # Spin the iterator until the next block is after this timeslot
        # (which means the current block is the one the timeslot is in).
        while next_start <= timeslot.start:
            this_start, this_name = next_start, next_name
            next_start, next_name = next(iterator)

        # There should always be a this_start, because there should always
        # be at least one block that starts on or before the show.
        # (TODO(mattbw): This is a possible configuration error, check there.)
        assert this_start is not None, 'Block start is None.'
        assert this_start < next_start, 'Block starts are in wrong order.'

        return (
            this_name,
            functools.partial(f, this_start, this_name, next_start, next_name)
        )

    # Make sure there's an initial "next block" for the first
    # invocation.
    return functools.partial(f, None, None, *next(iterator))
