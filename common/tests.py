"""Nose tests for lass.common.

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
import itertools
import pytz

import lass.common.mixins


aware = functools.partial(datetime.datetime, tzinfo=pytz.utc)


class TransientMock(lass.common.mixins.Transient):
    """Dummy class for checking properties of the 'Transient' mixin."""
    def __init__(self, effective_from, effective_to):
        self.effective_from = effective_from
        self.effective_to = effective_to


#
# Utility functions and instances for transient tests
#
early_day = functools.partial(aware, year=1984, month=4, day=5)
mid_day = functools.partial(aware, year=1991, month=12, day=31)
late_day = functools.partial(aware, year=2009, month=4, day=13)
days = (early_day, mid_day, late_day)

early_time = {'hour': 11, 'minute': 11, 'second': 11}
late_time = {'hour': 13, 'minute': 50, 'second': 0}
times = (early_time, late_time)

datetimes = [day(**time) for (day, time) in itertools.product(days, times)]

effective_from = mid_day(**early_time)
effective_to = mid_day(**late_time)

never_started = TransientMock(None, effective_to)
never_finished = TransientMock(effective_from, None)
sometimes_active = TransientMock(effective_from, effective_to)


def test_transient_test_sanity():
    """Makes sure the test setup for transient tests is sane."""
    assert datetimes, 'No datetimes have been generated.'
    assert effective_from in datetimes, 'effective_from not in datetimes.'
    assert effective_to in datetimes, 'effective_to not in datetimes.'

    assert any((datetime < effective_from for datetime in datetimes)), (
        'No datetimes before effective_from in datetimes.'
    )
    assert any((datetime < effective_to for datetime in datetimes)), (
        'No datetimes before effective_to in datetimes.'
    )
    assert any((effective_from < datetime for datetime in datetimes)), (
        'No datetimes after effective_from in datetimes.'
    )
    assert any((effective_to < datetime for datetime in datetimes)), (
        'No datetimes after effective_to in datetimes.'
    )

def test_transient_started_by():
    """Tests the 'started_by' method of lass.common.mixins.Transient."""
    # True when a transient has become effective on or before the
    # argument date.

    for datetime in datetimes:
        assert not never_started.started_by(datetime), (
            'Transient with no effective_from should never start.'
            )

        # Both of these should be the same case (the effective_to
        # shouldn't change the start conditions).
        for transient in (never_finished, sometimes_active):
            # When effective_from is given:
            #     started_by true IF AND ONLY IF datetime on or after
            #     effective_from.
            # -> test both implications.

            before_start = (datetime < transient.effective_from)
            started = transient.started_by(datetime)

            assert before_start or started, (
                'Transient has not started on a datetime ({}) on or '
                'after its effective_from ({}).'.format(
                    datetime,
                    transient.effective_from
                )
            )
            assert not (before_start and started), (
                'Transient has started on a datetime ({}) before '
                'its effective_from ({}).'.format(
                    datetime,
                    transient.effective_from
                )
            )


def test_transient_not_finished_by():
    """Tests the 'not_finished_by' method of
    lass.common.mixins.Transient.
    """
    # False when a transient has become ineffective on or before the
    # argument date.

    for datetime in datetimes:
        assert never_finished.not_finished_by(datetime), (
            'Transient with no effective_to should never finish.'
        )

        # Both of these should be the same case (the effective_from
        # shouldn't change the finish conditions).
        for transient in (never_started, sometimes_active):
            # When effective_from is given:
            #     not_finished_by true IF AND ONLY IF effective_to after
            #     datetime.
            # -> test both implications.

            after_finish = (transient.effective_to <= datetime)
            not_finished = transient.not_finished_by(datetime)

            assert after_finish or not_finished, (
                'Transient has finished on a datetime ({}) before '
                'its effective_to ({}).'.format(
                    datetime,
                    transient.effective_to
                )
            )
            assert not (after_finish and not_finished), (
                'Transient has not finished on a datetime ({}) on or '
                'after its effective_to ({}).'.format(
                    datetime,
                    transient.effective_to
                )
            )
