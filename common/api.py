"""Client frontend to the URY API.

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
import requests

import lass.common.config


class Error(Exception):
    """Error representing a failure to establish meaningful contact with
    the URY API.
    """
    pass


class NotFound(Exception):
    """Error thrown when the API is asked to retrieve a resource that
    does not exist.
    """
    pass


def get(resource, config=None, **params):
    """Sends a GET request to the URY API.

    Args:
        resource: The name of the resource in the API tree we wish to
            fetch, as a partial URL.  (Example: "/user/101".)
        config: The configuration that contains information about where
            and how the API can be contacted.

    Returns:
        The API's response, as a direct translation of the JSON received
        from the API (thus this will usually be a dict).

    Raises:
        APIError, if the API raises a 4xx or 5xx error.
    """
    config = api_config(config)

    payload = params_to_payload(params, config)
    url = resource_to_url(resource, config)

    response = requests.get(url, params=payload)
    raise_api_error_if_failure(response, resource, url)

    return response.json()


def api_config(config=None):
    """Retrieves a configuration set for the API.

    Due to the 'config' argument, this can be placed at the top of any
    function requiring API configuration to ensure an incoming config
    argument points to some configuration.

    Args:
        config: If this is present and not None, it is returned verbatim
            instead of fetching the config anew.

    Returns:
        A dictionary of API configuration.
    """
    if config is None:
        out_config = lass.common.config.from_yaml('sitewide/website')['api']
    else:
        out_config = config
    return out_config


def params_to_payload(params, config):
    """Converts a set of parameters into a payload for a GET or POST
    request.
    """
    base_payload = {config['param-api-key']: config['api-key']}
    return dict(base_payload, **params)


def raise_api_error_if_failure(response, resource, url):
    """Raises an API error if the response denotes a failure to talk
    to the API meaningfully."""
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as exc:
        cls = (
            NotFound
            if response.status_code == requests.codes.not_found
            else Error
        )
        raise cls(
            'Could not GET resource {} via {}.'.format(
                resource,
                url
            )
        ) from exc


def resource_to_url(resource, config):
    """Converts an API resource to its URL using the API configuration.
    """
    base = config['api-root']
    return '/'.join((base, resource))
