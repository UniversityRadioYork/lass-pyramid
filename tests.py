"""Nose tests for anything lying in the codebase root.

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

import lass.views

def test_get_streams():
    """Tests 'lass.views.get_streams'."""
    # Deliberately put configured streams in no particular order.
    config = {
        'streams': {
            'foo': {
                'format': 'RealPlayer',
                'mount': 'horse',
                'kbps': 200
            },
            'bar': {
                'format': 'MP3',
                'mount': 'camel',
                'kbps': 100
            },
            'baz': {
                'format': 'ogg',
                'mount': 'everest',
                'kbps': 9000
            }
        }
    }

    streams = lass.views.get_streams(config)

    # Check list for basic sanity.
    assert isinstance(streams, list), 'Did not get a list back.'
    assert len(streams) == 3, 'Incorrect response length.'

    last_kbps = None

    for stream in streams:
        assert 'name' in stream, 'Stream has no name.'
        assert 'kbps' in stream, 'Stream has no kbps.'

        # Make sure each stream in the result is in the config.
        name = stream['name']
        assert name in config['streams'], 'Bad name: {}.'.format(name)

        # Make sure all stream properties match up.
        for key, value in config['streams'][name].items():
            assert value == stream[key], 'Config mismatch on {}.'.format(key)

        # Make sure the streams are monotonically decreasing in quality.
        assert last_kbps is None or stream['kbps'] <= last_kbps, (
            'Streams are not sorted correctly: {}kbps > {}kbps '.format(
                stream['kbps'],
                last_kbps
            )
        )
        last_kbps = stream['kbps']
