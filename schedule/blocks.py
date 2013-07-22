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

    range_blocks = range_iter(conf['range_blocks'])

    range_block = None
    next_range_block_start, next_range_block = next(range_blocks)

    for timeslot in timeslots:
        # Range-based blocks
        while next_range_block_start is not None and (
            time_context.combine_as_local(
                timeslot.start.date(),
                next_range_block_start
            ) <= timeslot.start
        ):
            range_block = next_range_block
            next_range_block_start, next_range_block = next(range_blocks)

        # Name-based blocks
        name_block = None
        for pattern, block in conf['name_blocks']:
            if (
                hasattr(timeslot, 'text') and
                'title' in timeslot.text and
                fnmatch.fnmatch(
                    timeslot.text['title'][0].lower(),
                    pattern.lower()
                )
            ):
                name_block = block
                # Don't match against any other pattern; this allows exclusion
                # patterns to exist.
                break

        # Name blocks take precedence if available.
        block_name = name_block if name_block is not None else range_block
        timeslot.block = (
            None
            if block_name is None
            else dict(conf['blocks'][block_name], name=block_name)
        )


def range_iter(blocks):
    """Produces an iterator that returns blocks from the given range-block
    list.

    The iterator will produce 2-tuples of the form (active time, block name)
    where either element may be None (signifying no forthcoming block in the
    former case and no active range-block in the latter).

    Args:
        blocks: An iterable consisting of 3-tuples (or equivalents) of the form
            (hour, minute, name), in ascending chronological order from midnight
            and with hour and minute representing a local time at which the
            block referred to by 'name' is to be active.

    Returns:
        An infinte iterable that will provide the above tuples.
    """
    return itertools.chain(
        (
            (
                datetime.time(hour=int(h), minute=int(m), second=0),
                name
            ) for (h, m, name) in blocks
        ),
        itertools.repeat((None, None))
    )


def block_config():
    """Retrieves the default block configuration."""
    return lass.common.config.from_yaml('sitewide/blocks')
