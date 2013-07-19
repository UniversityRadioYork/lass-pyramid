"""Common functions for dealing with dates and/or times.

Yes, this module does define tools for working with local times.  This is
necessary for dealing with some aspects of schedule code, but we prefer to work
in UTC wherever possible, so only use the local time functions from template
logic or where absolutely necessary.

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
import functools

import pytz

import lass.common.config


def aware_now():
    """Returns an aware datetime representing the current time.

    This will be in UTC.

    Returns:
        A UTC aware datetime representing now.
    """
    return datetime.datetime.now(pytz.utc)


def start_on(date, date_config):
    """Returns the datetime representing the start of the schedule on a
    particular date.

    Args:
        date: The date on which the start should be calculated.
        date_config: The configuration for the date/time functions, as loaded
            from 'load_date_config'.

    Returns:
        a datetime whose date is 'date' and whose time is the start of the
        schedule day in the local timezone on that date.
    """
    return date_config['timezone'].localize(
        datetime.datetime.combine(
            date,
            date_config['schedule_start_time']
        )
    )


def local_midnight_on(date, date_config):
    """Returns the datetime representing the local midnight
    particular date.

    Args:
        date: The date on which the midnight should be calculated.
        date_config: The configuration for the date/time functions, as loaded
            from 'load_date_config'.

    Returns:
        a datetime whose date is 'date' and whose time is midnight in the local
        timezone on that date.
    """
    return date_config['timezone'].localize(
        datetime.datetime.combine(
            date,
            datetime.time(hour=0, minute=0, second=0)
        )
    )


def load_date_config():
    """Loads and pre-processes the website date configuration file."""
    raw_config = lass.common.config.from_yaml('sitewide/time')

    timezone = pytz.timezone(raw_config['timezone'])

    config = {
        'timezone': timezone,
        'schedule_start_time': datetime.time(
            hour=raw_config['schedule_start_hour']
        ),
        'second_year_terms': raw_config['second_year_terms']
    }

    # Add functions commonly used in templates into the config.
    configure = functools.partial(functools.partial, date_config=config)
    config.update(
        {
            'local_midnight_on': configure(local_midnight_on),
            'start_on': configure(start_on)
        }
    )
    return config


#
# These next two functions were purloined from
# http://stackoverflow.com/q/304256
#


def iso_year_start(iso_year):
    """The gregorian calendar date of the first day of the given ISO year."""
    fourth_jan = datetime.date(iso_year, 1, 4)
    delta = datetime.timedelta(fourth_jan.isoweekday()-1)
    return fourth_jan - delta


def iso_to_gregorian(iso_year, iso_week, iso_day):
    """Gregorian calendar date for the given ISO year, week and day."""
    year_start = iso_year_start(iso_year)
    return year_start + datetime.timedelta(
        days=iso_day-1,
        weeks=iso_week-1
    )
