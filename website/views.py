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

import functools
import pyramid
import requests

import lass.common.config
import lass.website.models


@pyramid.view.view_config(
    route_name='about',
    renderer='website/about.jinja2'
)
@pyramid.view.view_config(
    route_name='getinvolved',
    renderer='website/getinvolved.jinja2'
)
@pyramid.view.view_config(
    route_name='listen',
    renderer='website/listen.jinja2'
)
def static(_):
    """A view that can be used for static website pages."""
    return {}

@pyramid.view.view_config(
    route_name='signup',
    renderer='website/signup.jinja2'
)
def signup(request):
    """The view for processing a sign up"""
    config = lass.common.config.from_yaml('sitewide/website')['api']
    payload = {
        config['param-api-key']: config['api-key'],
        config['param-first-name']: request.params.get('first-name'),
        config['param-last-name']: request.params.get('last-name'),
        config['param-email']: request.params.get('email'),
        config['param-gender']: request.params.get('gender'),
        config['param-college']: request.params.get('college')
    }
    r = requests.post(config['create-user-url'], data=payload)
    r.raise_for_status()
    
    # Get the created ID
    j = r.json()
    id = j['memberid']
    
    for i in request.params.getall('interest'):
      payload = {
        config['param-api-key']: config['api-key'],
        config['param-subscribe-memberid']: id
      }
      r = requests.post(config['subscribe-url-base'] + i 
              + config['subscribe-url-suffix'], data=payload)
      r.raise_for_status()
    
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
    context = {
        'banners': lass.website.models.Banner.for_location('index')
    }

    for view in [
        box_podcast_raw,
        box_chart_raw,
        box_recommended_raw,
        box_news_raw,
        box_speech_raw
    ]:
        context.update(view())
    return context

@pyramid.view.notfound_view_config(
    renderer='errors/404.jinja2',
    append_slash=True
)
def not_found(request, *_):
    request.response.status = '404 Not Found'

    return {}


#
# Box views
#
# These come in two flavours: the "actual" view that renders the box
# fully, and the "raw" view that merely returns the template context
# the actual view uses.
#
# The latter is for serving for AJAX and iframes; the former is for
# merging into the home() view's context directly.
#


def box_chart_raw():
    """Raw view for the home page's charts box."""
    return lass.music.views.generic_chart('chart')


def box_recommended_raw():
    """Raw view for the home page's Recommended Listening box."""
    return lass.music.views.generic_chart('music')


def box_team_blog_raw(blog_name):
    """Raw view for the home page's team blog boxes."""
    return {
        blog_name: lass.teams.views.blog(blog_name)
    }


box_news_raw = functools.partial(box_team_blog_raw, 'news')
box_speech_raw = functools.partial(box_team_blog_raw, 'speech')


def box_podcast_raw():
    """Raw view for the home page's podcasts box."""
    podcasts = lass.uryplayer.views.podcast_list_query()[:5]
    lass.uryplayer.models.Podcast.annotate(podcasts)

    return {
        'podcasts': podcasts
    }
