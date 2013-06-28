"""The data models for the URY Player submodule of the URY website.

These data models are implemented using SQLAlchemy and contain no
website-specific code, and are theoretically transplantable into any Python
project.

Most notably missing from these models is any semblance of a "get URL" function
as this is defined at the template level.  This is not ideal, but is
deliberately done to separate data models from the website concepts.

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

import sqlalchemy

import lass.common
import lass.metadata
import lass.people.mixins


class URYPlayerModel(object):
    """Base for all schedule models."""
    __table_args__ = {'schema': 'uryplayer'}


class Podcast(
    lass.metadata.mixins.MetadataSubject,
    lass.people.mixins.PersonSubmittable,
    lass.people.mixins.Creditable,
    lass.Base,
    URYPlayerModel
):
    __tablename__ = 'podcast'
    query = lass.model_base.DBSession.query_property()

    id = sqlalchemy.Column(
        'podcast_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )
    file = sqlalchemy.Column(sqlalchemy.String(100), nullable=False)

    @classmethod
    def annotate(cls, podcasts):
        """Annotates a list of shows with their standard metadata and credits
        sets.

        Args:
            shows: A list of shows to annotate in-place.
        """
        cls.add_meta(podcasts, 'text', 'title', 'description', 'tags')
        cls.add_meta(podcasts, 'image', 'thumbnail_image', 'player_image')
        cls.add_credits(podcasts, with_byline_attr='byline')
