"""The data models for the Music submodule of the URY website.

These data models are implemented using SQLAlchemy and contain no
website-specific code, and are theoretically transplantable into any Python
project.

Most notably missing from these models is any semblance of a "get URL" function
as this is defined at the template level.  This is not ideal, but is
deliberately done to separate data models from the website concepts.

---

Copyright (c) 2013, University Madio York.
All rights reserved.

Redistribution and use in sourceand binary forms, with or without modification,
are permitted provided that the following conditions are met:

* Redistributins of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of Musonditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THECOPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. INNO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import itertools
import operator
import sqlalchemy

import lass.model_base
import lass.common
import lass.people.models


# These exist to speed up rec_Xlookup and similar definitions:
def lookup_id(name, direct_name=False):
    return sqlalchemy.Column(
        name if direct_name else '_'.join((name, 'code')),
        sqlalchemy.CHAR(1),
        primary_key=True,
        nullable=False
    )


def lookup_descr(name, direct_name=False):
    return sqlalchemy.Column(
        name if direct_name else '_'.join((name, 'descr')),
        sqlalchemy.Text,
        nullable=False
    )


#
# REC
#

class Genre(lass.model_base.Base):
    """A genre in the track database."""
    __tablename__ = 'rec_genrelookup'
    id = lookup_id('genre')
    description = lookup_descr('genre')


class Medium(lass.model_base.Base):
    """A type of record medium in the track database.

    Medium in this case means, for example, 'vinyl', 'CD' etc.
    """
    __tablename__ = 'rec_medialookup'
    id = lookup_id('media')
    description = lookup_descr('media')


class RecordFormat(lass.model_base.Base):
    """A type of record format in the track database.

    Format in this case means, for example, 'album' or 'single'.
    """
    __tablename__ = 'rec_formatlookup'
    id = lookup_id('format')
    description = lookup_descr('format')


class RecordStatus(lass.model_base.Base):
    """A type of cleanliness status in the track database."""
    __tablename__ = 'rec_statuslookup'
    id = lookup_id('status')
    description = lookup_descr('status')


class CleanStatus(lass.model_base.Base):
    """A type of cleanliness status in the track database."""
    __tablename__ = 'rec_cleanlookup'
    id = lookup_id('clean')
    description = lookup_descr('clean')


class Record(lass.model_base.Base):
    """A record in the track database."""
    __tablename__ = 'rec_record'

    id = sqlalchemy.Column(
        'recordid',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )

    status_id = sqlalchemy.Column(
        'status',
        sqlalchemy.ForeignKey(RecordStatus.id),
        nullable=False,
        server_default='o'
    )
    status = sqlalchemy.orm.relationship(RecordStatus)

    medium_id = sqlalchemy.Column(
        'media',
        sqlalchemy.ForeignKey(Medium.id),
        nullable=False
    )
    medium = sqlalchemy.orm.relationship(Medium)

    format_id = sqlalchemy.Column(
        'format',
        sqlalchemy.ForeignKey(RecordFormat.id),
        nullable=False
    )
    format = sqlalchemy.orm.relationship(RecordFormat)

    memberid_add = sqlalchemy.Column(
        sqlalchemy.ForeignKey(lass.people.models.Person.id),
        nullable=False
    )
    adder = sqlalchemy.orm.relationship(
        lass.people.models.Person,
        foreign_keys=[memberid_add]
    )

    memberid_lastedit = sqlalchemy.Column(
        sqlalchemy.ForeignKey(lass.people.models.Person.id)
    )
    last_editor = sqlalchemy.orm.relationship(
        lass.people.models.Person,
        foreign_keys=[memberid_lastedit]
    )

    title = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    artist = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    recordlabel = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    dateadded = sqlalchemy.Column(
        sqlalchemy.DateTime(timezone=True),
        nullable=False
    )
    datereleased = sqlalchemy.Column(sqlalchemy.Date)
    shelfnumber = sqlalchemy.Column(sqlalchemy.SmallInteger, nullable=False)
    shelfletter = sqlalchemy.Column(sqlalchemy.CHAR(1), nullable=False)
    datetime_lastedit = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))
    cdid = sqlalchemy.Column(sqlalchemy.String(8))
    location = sqlalchemy.Column(sqlalchemy.Text)
    promoterid = sqlalchemy.Column(sqlalchemy.Integer)


class Track(lass.model_base.Base):
    """A track in the track database."""
    __tablename__ = 'rec_track'

    id = sqlalchemy.Column(
        'trackid',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )

    clean = sqlalchemy.Column(
        sqlalchemy.ForeignKey(CleanStatus.id),
        nullable=False
    )
    cleanstatus = sqlalchemy.orm.relationship(CleanStatus)

    recordid = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey(Record.id),
        nullable=False
    )
    record = sqlalchemy.orm.relationship(Record)

    digitisedby = sqlalchemy.Column(
        sqlalchemy.ForeignKey(lass.people.models.Person.id)
    )
    digitiser = sqlalchemy.orm.relationship(lass.people.models.Person)

    artist = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    digitised = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        server_default='FALSE'
    )
    duration = sqlalchemy.Column(sqlalchemy.Integer)
    genre = sqlalchemy.Column(sqlalchemy.ForeignKey(Genre.id), nullable=False)
    intro = sqlalchemy.Column(sqlalchemy.Time, nullable=False)
    lastfm_verified = sqlalchemy.Column(
        sqlalchemy.Boolean,
        server_default='FALSE'
    )
    length = sqlalchemy.Column(sqlalchemy.Time, nullable=False)
    number = sqlalchemy.Column(sqlalchemy.SmallInteger, nullable=False)
    title = sqlalchemy.Column(sqlalchemy.Text, nullable=False)


#
# Tracklisting
#

class TracklistModel(lass.model_base.Base):
    """Base for all tracklisting models."""
    __abstract__ = True
    __table_args__ = {'schema': 'tracklist'}


class TrackSource(TracklistModel):
    """Source types for tracklisting."""
    __tablename__ = 'source'
    id = lookup_id('sourceid', direct_name=True)
    description = lookup_descr('source', direct_name=True)


class TrackState(TracklistModel):
    """State types for tracklisting."""
    __tablename__ = 'state'
    id = lookup_id('stateid', direct_name=True)
    description = lookup_descr('tate', direct_name=True)


class TrackListing(TracklistModel):
    """The main tracklisting entity."""
    __tablename__ = 'tracklist'

    id = sqlalchemy.Column(
        'audiologid',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )

    source_id = sqlalchemy.Column(
        'source',
        sqlalchemy.ForeignKey(TrackSource.id),
        nullable=False
    )
    source = sqlalchemy.orm.relationship(TrackSource)

    state_id = sqlalchemy.Column(
        'state',
        sqlalchemy.ForeignKey(TrackState.id)
    )
    state = sqlalchemy.orm.relationship(TrackState)

    # Will cause circular dependencies if the targets are not strings.
    timeslotid = sqlalchemy.Column(
        sqlalchemy.ForeignKey(
            'schedule.show_season_timeslot.show_season_timeslot_id'
        )
    )
    # lass.schedule.models.Timeslot will make a back-reference here called
    # timeslot

    timestart = sqlalchemy.Column(sqlalchemy.DateTime, nullable=False)
    timestop = sqlalchemy.Column(sqlalchemy.DateTime)
    bapsaudioid = sqlalchemy.Column(sqlalchemy.Integer)


class TrackListingLibraryTrack(TracklistModel):
    """A mapping between a track listing and record library entries."""
    __tablename__ = 'track_rec'

    audiologid = sqlalchemy.Column(
        sqlalchemy.ForeignKey(TrackListing.id),
        primary_key=True,
        nullable=False
    )
    listing = sqlalchemy.orm.relationship(TrackListing)

    recordid = sqlalchemy.Column(
        sqlalchemy.ForeignKey(Record.id),
        nullable=False
    )
    record = sqlalchemy.orm.relationship(Record)

    trackid = sqlalchemy.Column(sqlalchemy.ForeignKey(Track.id))
    track = sqlalchemy.orm.relationship(Track)


class TrackListingCustomTrack(TracklistModel):
    """An entry for a track listing that is not in the library."""
    __tablename__ = 'track_notrec'

    audiologid = sqlalchemy.Column(
        sqlalchemy.ForeignKey(TrackListing.id),
        primary_key=True,
        nullable=False
    )
    listing = sqlalchemy.orm.relationship(TrackListing)

    artist = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    album = sqlalchemy.Column(sqlalchemy.Text)
    label = sqlalchemy.Column(sqlalchemy.Text)
    trackno = sqlalchemy.Column(sqlalchemy.Integer)
    track = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    length = sqlalchemy.Column(sqlalchemy.DateTime)


#
# Music
#

class MusicModel(lass.model_base.Base):
    """Base for all Music models."""
    __abstract__ = True
    __table_args__ = {'schema': 'music'}


class Chart(lass.common.mixins.Type, MusicModel):
    """A type of chart."""
    __tablename__ = 'chart_type'
    query = lass.model_base.DBSession.query_property()

    id = sqlalchemy.Column(
        'chart_type_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )
    releases = sqlalchemy.orm.relationship('ChartRelease', backref='chart')

    @classmethod
    def latest(cls, chart_name, on_date=None):
        """Retrieves the latest chart with a given name.

        The chart will be pre-formatted into a list of rows in the form
        [Last Chart Position, Current Position, Track].

        If 'on_date' is given and not None, then the chart that was latest on
        that date will be retrieved instead.

        Args:
            chart_name: The name of the chart, for example 'music' (Recommended
                Listening) or 'chart' (the chart proper).
            on_date: The datetime for which the latest (relatively speaking)
                chart is sought.  If None, use the current datetime.
                (Default: None.)
        """
        if on_date is None:
            on_date = lass.common.time.aware_now()

        releases = lass.model_base.DBSession.query(
            ChartRelease.id
        ).join(
            cls
        ).filter(
            (cls.name == chart_name) &
            (ChartRelease.submitted_at <= on_date)
        ).order_by(
            sqlalchemy.desc(ChartRelease.submitted_at)
        ).limit(2)

        rows = lass.model_base.DBSession.query(
            ChartRelease.id,
            ChartRow.position.label('position'),
            Track
        ).join(
            ChartRow.track,
            ChartRow.release
        ).filter(
            ChartRelease.id.in_(releases)
        ).order_by(
            sqlalchemy.desc(ChartRelease.submitted_at),
            sqlalchemy.asc(ChartRow.position)
        ).all()

        # Split rows into releases
        # Rows should come out as (release, position, track)
        raw = [
            list(v)
            for _, v in itertools.groupby(rows, operator.itemgetter(0))
        ]

        try:
            current = raw[0]
        except IndexError:
            result = None
        else:
            try:
                last = raw[1]
            except IndexError:
                last = []

            # Work out last positions in a slightly interesting way that'll
            # fall over mildly if the same track appears multiple times on the
            # previous week chart.
            last_posns = {track.id: position for _, position, track in last}

            result = [
                [last_posns.get(track.id), position, track]
                for _, position, track in current
            ]

        return result


class ChartRelease(lass.common.mixins.Submittable, MusicModel):
    """A release of a particular chart type."""
    __tablename__ = 'chart_release'

    id = sqlalchemy.Column(
        'chart_release_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )
    chart_type_id = sqlalchemy.Column(
        sqlalchemy.ForeignKey(Chart.id),
        nullable=False
    )
    rows = sqlalchemy.orm.relationship('ChartRow', backref='release')
    # Backref 'chart' from Chart.releases


class ChartRow(MusicModel):
    """A row in a chart release."""
    __tablename__ = 'chart_row'

    id = sqlalchemy.Column(
        'chart_row_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )
    chart_release_id = sqlalchemy.Column(
        sqlalchemy.ForeignKey(ChartRelease.id),
        nullable=False
    )

    position = sqlalchemy.Column(sqlalchemy.SmallInteger, nullable=False)
    trackid = sqlalchemy.Column(sqlalchemy.ForeignKey(Track.id))
    track = sqlalchemy.orm.relationship(Track, lazy='joined')
    # Backref 'release' from ChartRelease.rows
