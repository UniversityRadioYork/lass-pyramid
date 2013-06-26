"""Common functions for dealing with dates and/or times.

Yes, this module does define tools for working with local times.  This is
necessary for dealing with some aspects of schedule code, but we prefer to work
in UTC wherever possible, so only use the local time functions from template
logic or where absolutely necessary.
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
    raw_config = lass.common.config.from_yaml('sitewide/time')

    timezone = pytz.timezone(raw_config['timezone'])

    config = {
        'timezone': timezone,
        'schedule_start_time': datetime.time(
            hour=raw_config['schedule_start_hour']
        ),
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
