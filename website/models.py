"""Models for the Website submodule of the URY website.

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

import lass.model_base
import lass.common.mixins
import lass.people.mixins


class WebsiteModel(lass.model_base.Base):
    """Base for models in the website schema."""
    __abstract__ = True
    __table_args__ = {'schema': 'website'}


class BannerType(lass.common.mixins.Type, WebsiteModel):
    __tablename__ = 'banner_type'

    id = sqlalchemy.Column(
        'banner_type_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )


class BannerCampaign(
    lass.people.mixins.Approvable,
    lass.people.mixins.Ownable,
    lass.common.mixins.Transient,
    WebsiteModel
):
    """A run of a banner on a website location, into which multiple
    banner slots can be entered.

    """
    __tablename__ = 'banner_campaign'

    id = sqlalchemy.Column(
        'banner_campaign_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )

    # These foreign keys are specified manually via string to prevent circular
    # references between Banner and BannerCampaign.  Not ideal!
    banner_location_id = sqlalchemy.Column(
        sqlalchemy.ForeignKey('website.banner_location.banner_location_id')
    )
    location = sqlalchemy.orm.relationship('BannerLocation')

    banner_id = sqlalchemy.Column(
        sqlalchemy.ForeignKey('website.banner.banner_id')
    )
    banner = sqlalchemy.orm.relationship('Banner')

    timeslots = sqlalchemy.orm.relationship('BannerTimeslot')


class Banner(WebsiteModel):
    __tablename__ = 'banner'

    id = sqlalchemy.Column(
        'banner_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )

    alt = sqlalchemy.Column(sqlalchemy.Text)

    campaigns = sqlalchemy.orm.relationship(BannerCampaign)

    # The URI that the banner links to when clicked;
    # if this is empty, the banner will not be clickable.
    image = sqlalchemy.Column(sqlalchemy.String(100))
    target = sqlalchemy.Column(sqlalchemy.String(200))

    # Type doesn't seem to be used, but is a relic of the schema.
    banner_type_id = sqlalchemy.Column(
        sqlalchemy.ForeignKey(BannerType.id)
    )
    type = sqlalchemy.orm.relationship(BannerType)

    @classmethod
    def for_location(cls, location, when=None):
        """Retrieves the set of banners to show on the given
        location at the given datetime.

        Args:
            location: The name of a BannerLocation.
            when: An aware datetime representing the time to retrieve banners for.
                (Default: now.)
        Returns:
            A list of objects of this class to show on the given location at the
            given time.
        """
        if not when:
            when = lass.common.time.aware_now()

        return lass.model_base.DBSession.query(
            cls
        ).filter(
            # Pick up banners for this location that...
            (BannerLocation.name == location) & cls.campaigns.any(
                # ...have an active campaign running that...
                lass.common.rdbms.transient_active_on(
                    when,
                    BannerCampaign.__table__
                ) & BannerCampaign.timeslots.any(
                    # ...has a timeslot we're currently in.
                    (BannerTimeslot.day == when.isoweekday()) &
                    (BannerTimeslot.start_time <= when.time()) &
                    (BannerTimeslot.finish_time > when.time())
                    # (Phew!)
                )
            )
        )


class BannerLocation(lass.common.mixins.Type, WebsiteModel):
    """A location on the website that a banner campaign can be run
    in.
    """
    __tablename__ = 'banner_location'

    id = sqlalchemy.Column(
        'banner_location_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )


class BannerTimeslot(
    lass.people.mixins.Approvable,
    lass.people.mixins.Ownable,
    WebsiteModel
):
    """A timeslot on a banner campaign, marking a period of time on
    a given weekday for the banner to appear in the campaign
    rotation.

    """
    __tablename__ = 'banner_timeslot'

    id = sqlalchemy.Column(
        'banner_timeslot_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )
 

    banner_campaign_id = sqlalchemy.Column(
        sqlalchemy.ForeignKey(BannerCampaign.id)
    )
    campaign = sqlalchemy.orm.relationship(BannerCampaign)

    # The day of the week on which this banner slot will run, with Monday as day
    # 1 and Sunday as day 7.
    day = sqlalchemy.Column(sqlalchemy.SmallInteger)

    start_time = sqlalchemy.Column(sqlalchemy.Time(timezone=True))
    finish_time = sqlalchemy.Column('end_time', sqlalchemy.Time(timezone=True))
