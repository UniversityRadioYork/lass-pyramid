"""Views for the URYPlayer submodule of the URY website.

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
import math

import pyramid
import sqlalchemy

import lass.common.view_helpers
import lass.metadata.models
import lass.model_base
import lass.uryplayer.models


@pyramid.view.view_config(
    route_name='uryplayer'
)
def uryplayer(request):
    """The main URYPlayer page."""
    # Currently redirects to podcasts.
    # These are kept separate in case we ever branch out to something else under
    # the URYPlayer branding.
    raise pyramid.httpexceptions.HTTPFound(
        location=request.route_url('uryplayer-podcasts')
    )


@pyramid.view.view_config(
    route_name='uryplayer-podcasts',
    renderer='uryplayer/podcasts.jinja2'
)
def podcasts(request):
    """Displays a list of podcasts."""
    return lass.common.view_helpers.media_list(
        request,
        lass.model_base.DBSession.query(
            lass.uryplayer.models.Podcast
        ).options(
            sqlalchemy.orm.subqueryload('credits')
        ).order_by(
            sqlalchemy.desc(lass.uryplayer.models.Podcast.submitted_at)
        )
    )


@pyramid.view.view_config(
    route_name='uryplayer-podcast-detail',
    renderer='uryplayer/podcast_detail.jinja2'
)
def podcast_detail(request):
    """Displays detail about a podcast."""

    return lass.common.view_helpers.detail(
        request,
        id_name='podcastid',
        source=lass.model_base.DBSession.query(
            lass.uryplayer.models.Podcast
        ).options(
            sqlalchemy.orm.joinedload('credits')
        ),
        target_name='podcast'
    )


@pyramid.view.view_config(
    route_name='uryplayer-podcast-search',
    renderer='uryplayer/podcast-search.jinja2'
)
def search(request):
    """Performs a search if a query is given, or allows the user to do so."""

    return lass.common.view_helpers.search(
        request,
        lass.uryplayer.models.Podcast,
        lambda id: request.route_url('uryplayer-podcast-detail', podcastid=id)
    )
