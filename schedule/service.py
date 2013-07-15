"""Functions for ascertaining the type of service the station is outputting.

By "service" we mean: is there any scheduled programming running today?  Can
people listen on the radio or are we just outputting to streams?  Are the
streams down?  And, if we are outputting programming, which season term is in
use?

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

import lass.common.time
import lass.schedule.models


# Allowed service types; see service_type() for documentation
SERVICE_TYPES = (
    'up',
    'sustainer',
    'emergency',
    'down'
)


class State(object):
    """Lazy loading and caching interface for retrieving service status
    information.
    """
    def __init__(self, at_time=None, service_config=None):
        """Initialises a LazyState.

        Args:
            at_time: The time at which we are checking the service state.
                (Default: None, which signifies using the current date.)
            service_config: The service configuration, primarily used for
                overrides and maintenance explanation.
                If None, the configuration will be read from file.
                (Default: None.)

        Returns:
            A ServiceState object set up for the given time.
        """
        self.at_time = at_time
        self._cache = {}

        self.config = service_config if service_config else read_config()

    @property
    def term(self):
        """Returns the term any active show seasons will belong to."""
        return self._lazy(
            'term',
            (lambda: lass.schedule.models.Term.on(self.at_time))
        )

    @property
    def can_listen(self):
        """Returns whether or not the station is formally listenable to."""
        return (self.service_type in 'down')

    @property
    def programming_available(self):
        """Returns whether or not the station is providing programming."""
        return (self.service_type == 'normal')

    @property
    def service_type(self):
        """Returns the current type of service provided by the station."""
        return self._lazy(
            'service_type',
            (lambda: service_type(self.at_time, self.term, self.config))
        )

    @property
    def maintenance_notice(self):
        """Returns any maintenance notice set.

        Note that this won't work properly if inspecting the service state of
        any time other than None (now), because maintenance notices have no
        history attached.
        """
        maintenance = self.config.get('maintenance')
        return (
            maintenance
            if maintenance and maintenance.get('active', False)
            else None
        )

    def _lazy(self, key, value_function):
        """Populates a lazy attribute 'key' using 'value_function' if unset."""
        if key not in self._cache:
            self._cache[key] = value_function()
        return self._cache[key]


def service_type(at_time=None, term=None, service_config=None):
    """Returns the type of service provided by the station at the given time.

    If at_time is None (in other words, current service type is desired), then
    manual overrides may be checked to provide extra detail; otherwise the
    "expected" service type based on the date alone is used.

    Possible return values (enumerated in 'SERVICE_TYPES') include:
        'normal': The station is providing normal service (scheduled
            programming and no emergency overrides)
        'emergency': The station is currently broadcasting emergency
            programming.  (Currently unused.)
        'sustainer': The station is broadcasting but no actual programming is
            being aired; listeners can tune in but all they will hear is
            sustainer.  (For URY, this is usually the case in Autumn and Spring
                vacations.)
        'down': The station is formally not transmitting at all; no listening
            should be allowed.  (For URY, this is usually the case during the
                Summer vacation.)

    Args:
        at_time: The aware datetime for which the service type is desired.
            A value of None implies the current time, and allows current manual
            overrides to be taken into account, if any.  (Default: None.)
        term: The term active during 'at_time', used for deciding the service
            type in the absence of manual overrides.  Provided to prevent
            duplicate queries when the term is already known; if None then the
            term will be found using 'lass.schedule.models.Term.on'.
            (Default: None.)
        service_config: The service configuration to use for manual overrides;
            if None, the config will be read from scratch.  Provided to prevent
            duplicate reading.  (Default: None.)

    Returns:
        A string matching one of the above possible return values and
        describing the current service type.
    """
    if at_time is None:
        at_time = lass.common.time.aware_now()
        use_overrides = True
    else:
        # Don't allow overrides if we have a time specified.
        # This is because currently overrides have no history
        use_overrides = False

    if term is None:
        term = lass.schedule.models.Term.on(at_time)
    if service_config is None:
        service_config = read_config

    if use_overrides:
        # Try manual override
        service_type = service_config.get('service_type')
    else:
        service_type = None

    if service_type not in SERVICE_TYPES:
        # No sane manual override present
        # Get the service type through term inspection.

        if term is None:
            # If we can't get a term, that implies that the database hasn't been
            # updated.  Ideally, we should make a log of this at some point.
            service_type = 'down'
        elif term.end > at_time:
            # Inside a term, which to us implies programming is happening.
            service_type = 'normal'
        elif term.name.lower() == 'summer':
            # Inside the summer break
            service_type = 'down'
        else:
            # Inside spring or autumn break
            service_type = 'sustainer'
    return service_type


def read_config():
    """Reads in the service configuration from file."""
    return lass.common.config.from_yaml('sitewide/service')
