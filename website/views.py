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


class SignupError(Exception):
    """Exception marking an error found during signup."""
    def __init__(self, stage, details):
        """Creates a SignupError.

        Args:
            stage: A string defining the stage of signup at which the
                error occurred.
            details: An object (expected type dependent on stage)
                providing more details about the error.

        Returns:
            A SignupError.
        """
        self.stage = stage
        self.details = details


@pyramid.view.view_config(
    route_name='signup',
    renderer='website/signup.jinja2'
)
def signup(request):
    """The view for processing a sign up"""
    config = lass.common.config.from_yaml('sitewide/website')['api']

    try:
        create_payload = signup_validate_create(config, request.params)
        member_id = signup_create_user(config, create_payload)

        subscribe_payload, interest_urls = (
            signup_validate_subscribe(config, request.params, member_id)
        )
        context = (
            signup_subscribe_user(subscribe_payload, interest_urls)
        )
    except SignupError as error:
        context = {'error': error.stage, 'details': error.details}

    return context


def signup_validate_create(config, params):
    """Validates the incoming signup and returns a payload for it.

    Args:
        config: The API configuration.
        params: The raw HTTP request parameter multidict containing the
            signup form information.

    Returns:
        A dictionary that can be used as the payload for a user creation
        API request.

    Raises:
        SignupError if the arguments fail validation.
    """
    payload = {config['param-api-key']: config['api-key']}
    errors = []

    trimmed_params = {key: value.strip() for key, value in params.items()}

    for key, name in (
        ('first-name', 'a first name'),
        ('last-name', 'a last name'),
        ('email', 'an email address'),
        ('gender', 'a gender'),
        ('college', 'a college')
    ):
        if not trimmed_params.get(key, ''):
            errors.append('You have not provided {}.'.format(name))
        else:
            payload[config['param-' + key]] = trimmed_params[key]

    if not errors:
        try:
            int(trimmed_params['college'])
        except ValueError:
            errors.append(
                (
                    "The college code we've received doesn't look right.  "
                    'This is probably a problem on our end.'
                ).format(key)
            )
        if trimmed_params['gender'] not in 'omf':
            errors.append(
                (
                    "The gender code we've received doesn't look right.  "
                    'This is probably a problem on our end.'
                ).format(key)
            )

    if errors:
        raise SignupError('validate', errors)

    return payload


def signup_create_user(config, payload):
    """Performs the user creation part of the signup process."""
    json = signup_request('create', config['create-user-url'], payload)
    return json['memberid']


def signup_validate_subscribe(config, params, member_id):
    """Validates the incoming subscription and returns a payload for it.

    Args:
        config: The API configuration.
        params: The raw HTTP request parameter multidict containing the
            signup form information.
        member_id: The ID of the subscribing member.

    Returns:
        A tuple containing a dictionary that can be used as the payload
        for a user creation API request, and secondly an iterable of
        URLs representing the targets of each requested subscription.

    Raises:
        SignupError if the arguments fail validation.
    """
    errors = []
    payload = {
        config['param-api-key']: config['api-key'],
        config['param-subscribe-memberid']: member_id
    }

    try:
        member_id_int = int(member_id)
    except ValueError:
        errors.append(
            'The member ID we received is not in the correct format.  '
            'This is almost certainly a bug in our website.'
        )
        member_id_int = None
    else:
        if member_id_int < 0:
            errors.append(
                'We were given a negative member ID when signing you up.  '
                'This is almost certainly a bug in our website.'
            )

    interests = []
    if 'interest' in params:
        for interest_id in params.getall('interest'):
            try:
                interest_id_int = int(interest_id)
            except ValueError:
                errors.append(
                    'The data we received about your interests appears '
                    'not to have reached us properly.  This is almost'
                    'certainly a bug in our signup form.'
                )
            else:
                if interest_id_int < 0:
                    errors.append(
                        'We were given a negative interest code from the '
                        'signup form.  This is almost certainly a bug in our '
                        'signup form.'
                    )
                else:
                    interests.append(interest_id)

    base = config['subscribe-url-base']
    suffix = config['subscribe-url-suffix']
    interest_urls = (
        ''.join((base, interest, suffix)) for interest in interests
    )

    if errors:
        raise SignupError('validate', errors)

    return payload, interest_urls


def signup_subscribe_user(payload, interest_urls):
    """Performs the subscription part of the signup process."""
    for interest_url in interest_urls:
        signup_request('subscribe', interest_url, payload)

    return {}


def signup_request(stage, url, payload):
    """Sends a request to the signup API."""
    response = requests.post(url, data=payload)
    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        raise SignupError(stage, response.json()['message'])
    return response.json()


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
