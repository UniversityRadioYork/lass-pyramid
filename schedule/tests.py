"""Nose tests for the Schedule submodule.

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

import functools
import unittest.mock

import lass.common.time
import lass.schedule.blocks


TEST_BLOCK_CONFIG = {
    'blocks': {
        'Test1': {
            'type': 'test_a'
        },
        'Test2': {
            'type': 'test_a'
        },
        'Test3': {
            'type': 'test_b'
        }
    },
    'range_blocks': [
        # Hour, minute, block
        [0, 0, 'Test1'],
        [7, 0, None],
        [9, 0, 'Test2'],
        [11, 0, None],
        [12, 0, 'Test3'],
        [14, 0, None],
        [19, 0, 'Test2'],
        [21, 0, 'Test1'],
    ],
    'name_blocks': [
        ['explicit name', 'Test1'],
        ['start*', 'Test2'],
        ['*finish', 'Test3'],
        ['exclude middle test', None],
        ['*middle*', 'Test1'],
        ['range[0123456789]', 'Test2']
    ]
}


#
# lass.schedule.blocks
#

def test_name_block_match():
    """Tests 'lass.schedule.block.name_block_match'."""
    timeslot = unittest.mock.MagicMock()
    timeslot.text = {'title': ['The Quick Brown Fox Show']}

    match = functools.partial(
        lass.schedule.blocks.name_block_match,
        timeslot
    )

    # Should match against itself, obviously.
    assert match('The Quick Brown Fox Show')

    # Case insensitivity should apply.
    assert match('THE QUICK BROWN FOX SHOW')
    assert match('the quick brown fox show')

    # Should not match substrings or as a substring without *.
    assert not match('Quick Brown Fox')
    assert not match('Introducing The Quick Brown Fox Show')

    # Should match against a substring with *.
    assert match('The Quick Brown*')
    assert match('*Quick Brown Fox*')
    assert match('*Brown Fox Show')

    # Should match character classes too, explicitly at least.
    assert match('The Quick Brown F[ao]x Show')

    # Should match wildcard...
    assert match('*')

    # And not match empty.
    assert not match('')


def test_range_iter():
    """Tests 'lass.schedule.block.range_iter'."""
    blocks = TEST_BLOCK_CONFIG['range_blocks']
    time_context = lass.common.time.TimeContext('Europe/London', [], 7)
    start_date = time_context.start_on(
        time_context.schedule_date_of(lass.common.time.aware_now())
    )

    r = lass.schedule.blocks.range_iter(
        blocks,
        start_date,
        time_context
    )

    # Should yield (datetime, name) for each (hour, minute, name).
    # Go around the list twice to make sure the iterator repeats itself.
    for hour, minute, name in (blocks + blocks):
        iter_datetime, iter_name = next(r)

        assert iter_name == name
        assert iter_datetime.hour == hour
        assert iter_datetime.minute == minute
