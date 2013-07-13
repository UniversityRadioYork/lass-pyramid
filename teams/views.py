"""Views for the Teams submodule of the URY website.

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
import feedparser

import lass.common.config


# Redirects from old team pages.

@pyramid.view.view_config(route_name='speech')
def speech_old(request):
    """Redirects to the new Speech microsite."""
    raise pyramid.httpexceptions.HTTPMovedPermanently(
        location=request.route_url('teams-speech')
    )


@pyramid.view.view_config(route_name='news')
def news_old(request):
    """Redirects to the new News microsite."""
    raise pyramid.httpexceptions.HTTPMovedPermanently(
        location=request.route_url('teams-news')
    )


# End redirects.

@pyramid.view.view_config(
    route_name='teams-news',
    renderer='teams/news.jinja2'
)
def news(request):
    """Renders the News microsite."""
    return blog('news')


@pyramid.view.view_config(
    route_name='teams-speech',
    renderer='teams/speech.jinja2'
)
def speech(request):
    """Renders the Speech microsite."""
    return blog('speech')


def blog(name):
    """Produces a view response dictionary for the blog of the given name.

    Args:
        name: The name of the blog as it appears in the blog configuration.

    Returns:        
        A dictionary ready to pass, straight or augmented, into a view renderer.
    """
    blog_config = lass.common.config.from_yaml('sitewide/blogs')[name]
    
    return { 
        'blog': blog_config,
        'get_posts': functools.partial(
            get_blog_from_feed,
            feed=blog_config['feed']
        )
    }


def get_blog_from_feed(feed, limit=None):
    """Retrieves blog posts from an RSS or Atom feed."""
    return feedparser.parse(feed)['entries'][:limit]
