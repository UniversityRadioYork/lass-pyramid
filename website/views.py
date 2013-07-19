"""Views for the Website submodule of the URY website.

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

import pyramid

import lass.common.config
import lass.website.models


@pyramid.view.view_config(
    route_name='about',
    renderer='website/about.jinja2'
)
@pyramid.view.view_config(
    route_name='listen',
    renderer='website/listen.jinja2'
)
def static(_):
    """A view that can be used for static website pages."""
    return {}


@pyramid.view.view_config(
    route_name='contact',
    renderer='website/contact.jinja2'
)
def contact(_):
    """The view for the Contact Us page."""
    return lass.common.config.from_yaml('sitewide/contacts')


@pyramid.view.view_config(
    route_name='home',
    renderer='website/index.jinja2'
)
def home(_):
    """The view for the index page."""
    return {
        'banners': lass.website.models.Banner.for_location('index')
    }


@pyramid.view.notfound_view_config(
    renderer='errors/404.jinja2',
    append_slash=True
)
def not_found(request, *_):
    request.response.status = '404 Not Found'

    return {}
