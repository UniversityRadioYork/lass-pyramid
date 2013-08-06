"""The schedule filler system.

Filling is the process of converting a list of scheduled timeslots which
may contain gaps into a continuous, gapless list; gaps are removed by
adding phony "filler" timeslots, which represent times where the station
is broadcasting sustainer programming.

The filler show is not stored in any form of database, but is instead
configured directly from a sitewide configuration file, "filler.yml".
This contains the filler show's metadata, amongst other things.

---

Copyright (c) 2013, University Radio York.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import datetime
import functools

import lass.common.config
import lass.schedule.models


ZERO = datetime.timedelta(seconds=0)


class FillerTimeslot(lass.schedule.models.BaseTimeslot):
    """An object representing a filler timeslot.

    Filler timeslots are mostly compatible with regular timeslots, but
    have pre-applied "fake" metadata, and have no attached seasons or
    shows.
    """
    is_filler = True
    is_collapsible = True

    def __init__(self, start, duration, metadata={}, block=None):
        super().__init__(start, duration)
        for attr, contents in metadata.items():
            setattr(self, attr, contents)

        self.block = block


def filler_from_config():
    """Creates a filler function that creates fake filler timeslots with
    metadata taken from the website's configuration files (specifically
    'sitewide/filler.yml'.
    """
    filler_config = lass.common.config.from_yaml('sitewide/filler')
    return functools.partial(
        FillerTimeslot,
        metadata=filler_config['metadata'],
        block=filler_config['block']
    )


#
# Filling algorithm
#


def fill(timeslots, filler, start, finish):
    """Fills any gaps in the given timeslot list with filler slots,
    such that the list is fully populated from the given start time
    to the given end time.

    Args:
        timeslots: The list of timeslots, may be empty.
        start: The datetime at which the filled timeslot list should start.
        finish: The datetime at which the filled timeslot list should finish.
    """
    if start > finish:
        raise ValueError('Start time is after finish time.')

    current_time = start
    filled = []
    unplaced = iter(timeslots)

    while current_time < finish:
        timeslot = next(unplaced, None)
        next_time = min(finish, timeslot.start) if timeslot else finish
        gap = next_time - current_time

        if gap < ZERO:
            raise ValueError(
                'Negative gap ({} between {} and {}, next ts: {}).'.format(
                    gap, current_time, next_time,
                    None if timeslot is None else timeslot.text['title'][0]
                )
            )
        elif gap > ZERO:
            filled.append(filler(current_time, gap))
            current_time = next_time
        # If no gap, don't fill!

        if timeslot:
            filled.append(timeslot)
            current_time = timeslot.finish

    return filled
