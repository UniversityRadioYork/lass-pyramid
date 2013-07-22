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

import pytz

import lass.common.config


def aware_now():
    """Returns an aware datetime representing the current time.

    This will be in UTC.

    Returns:
        A UTC aware datetime representing now.
    """
    return datetime.datetime.now(pytz.utc)


class TimeContext(object):
    """An object representing the context in which local date/time operations
    can occur.
    """

    def __init__(self, timezone, second_year_terms, schedule_start_time):
        """Initialises the TimeContext.

        Args:
            timezone: Either a string representing the Olson timezone used for
                local time operations, or a tzinfo object representing the same.
            second_year_terms: A list of names of terms for which the academic
                year is one less than the calendar year.
            schedule_start_time: Either a number representing the (local) hour
                at which the schedule begins each day, or a naive datetime
                representing the same.

        Returns:
            A TimeContext representing the above context.
        """
        if isinstance(timezone, str):
            self.timezone = pytz.timezone(timezone)
        else:
            self.timezone = timezone

        if isinstance(schedule_start_time, int):
            self.schedule_start_time = datetime.time(
                hour=schedule_start_time,
                minute=0,
                second=0
            )
        else:
            self.schedule_start_time = schedule_start_time

        self.second_year_terms = second_year_terms
        self.midnight = datetime.time(hour=0, minute=0, second=0)
        self.one_day = datetime.timedelta(days=1)

    def local_now(self):
        """Returns the current datetime in local (aware) time.

        Returns:
            An aware datetime representing now in this TimeContext's local
            timezone.
        """
        return self.localise(aware_now())

    def localise(self, dt):
        """Converts an aware datetime to local (aware) time.

        Args:
            dt: The datetime to convert to a local datetime.

        Returns:
            The datetime 'dt' in the appropriate timezone for website local time.
        """
        return dt.astimezone(self.timezone)

    def shift_local(self, datetime, delta):
        """Moves a local datetime by a timedelta, taking into account DST.

        Args:
            datetime: An aware, local datetime.
            delta: A timedelta by which the datetime should be shifted.

        Returns:
            The result of moving datetime by 'delta' amount of local time.  When
            applying over timezone boundaries, the effect of DST will be
            compensated for (for example, midnight BST + 4 hours = 4am GMT).
        """
        naive = datetime.replace(tzinfo=None)
        new_naive = naive + delta
        return self.timezone.localize(new_naive)

    def combine_as_local(self, date, time):
        """Combines a naive date and time and interprets as an aware datetime.

        This is useful for saying "give me the datetime on DATE at whatever
        TIME means in the timezone for that date."

        Args:
            date: The date concerned.
            time: The naive time, to be interpreted in whichever local timezone
                is in effect on 'date'.  This can be ambiguous in the face of an
                imminent timezone change; use with caution.
        Returns:
            The date time representing 'time' local time on 'date'.
        """
        return self.timezone.localize(datetime.datetime.combine(date, time))

    def start_on(self, date):
        """Returns the datetime representing the start of the schedule on a
        particular date.

        Args:
            date: The date on which the start should be calculated.

        Returns:
            a datetime whose date is 'date' and whose time is the start of the
            schedule day in the local timezone on that date.
        """
        return self.combine_as_local(date, self.schedule_start_time)

    def local_midnight_on(self, date):
        """Returns the datetime representing the local midnight
        particular date.

        Args:
            date: The date on which the midnight should be calculated.

        Returns:
            A datetime whose date is 'date' and whose time is midnight in the
            local timezone on that date.
        """
        return self.combine_as_local(date, self.midnight)

    def schedule_date_of(self, datetime):
        """Return the date on which an aware datetime falls in the schedule.

        Because the schedule need not start at midnight, the actual date and
        schedule date may differ by up to one day.

        Args:
            datetime: The aware datetime (timezone need not matter) whose
                corresponding schedule date is sought.

        Returns:
            A date (not a datetime) representing the schedule day on which the
            datetime lands.
        """
        local = self.localise(datetime)

        date = local.date()

        # Get the start of programming on the same local-time calendar day as
        # the input datetime.  We need this because the input datetime might be
        # before this time (and thus in the *day before*'s schedule)!
        day_start = self.start_on(date)

        # Correct for the above observation
        return date if local >= day_start else (date - self.one_day)


def context_from_config():
    """Creates a TimeContext from the time configuration file."""
    return TimeContext(**(lass.common.config.from_yaml('sitewide/time')))


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
