"""The data models for the Schedule submodule of the URY website.

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
import lass.music
import lass.model_base
import lass.people.mixins


class ShowQuery(sqlalchemy.orm.Query):
    """Extended version of Query with methods for easy querying of Shows.
    """
    def in_showdb(self):
        """Filters this Query down to shows whose type allows them to have
        ShowDB entries.

        Returns:
            This query, filtered to show only shows with ShowDB entries, as
            defined by their ShowType.
        """
        return self.filter(ShowType.has_showdb_entry)

    def public(self):
        """Filters this Query down to public shows only.
        
        Returns:
            This query, filtered to show only public shows as defined by their
            ShowType.
        """
        return self.filter(ShowType.is_public)

    def private(self):
        """Filters this Query down to private shows only.
        
        Returns:
            This query, filtered to exclude public shows as defined by their
            ShowType.
        """
        return self.exclude(ShowType.is_public)

    def scheduled(self):
        """Filters this Query down to shows that have scheduled slots.
        
        Returns:
            This query, filtered to show only shows (public or otherwise) that
            have scheduled timeslots.
        """
        return self.filter(Show.seasons.any(Season.timeslots.any()))


class ScheduleModel(lass.model_base.Base):
    """Base for all schedule models."""
    __abstract__ = True
    __table_args__ = {'schema': 'schedule'}


class ShowType(
    lass.common.mixins.Type,
    ScheduleModel
):
    """A type of show in the schedule.
    
    The URY schedule, in addition to normal shows, also tracks various
    show-like entities such as demos and reservations, as well as filler slots
    (the URY Jukebox).

    ShowTypes exist to allow these various types of show entity to be
    disambiguated, and the behaviour of each type to be specified in a
    fine-grained manner.
    """
    __tablename__ = 'show_type'

    id = sqlalchemy.Column(
        'show_type_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )
    is_public = sqlalchemy.Column(
        'public',
        sqlalchemy.Boolean,
        server_default='TRUE'
    )
    has_showdb_entry = sqlalchemy.Column(
        sqlalchemy.Boolean,
        server_default='TRUE'
    )
    is_collapsible = sqlalchemy.Column(
        sqlalchemy.Boolean,
        server_default='FALSE'
    )
    can_be_messaged = sqlalchemy.Column(
        sqlalchemy.Boolean,
        server_default='FALSE'
    )


class Show(
    lass.metadata.mixins.MetadataSubject,
    lass.people.mixins.PersonSubmittable,
    lass.people.mixins.Creditable,
    ScheduleModel
):
    __tablename__ = 'show'
    query = lass.model_base.DBSession.query_property(query_cls=ShowQuery)

    id = sqlalchemy.Column(
        'show_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )

    type = sqlalchemy.orm.relationship('ShowType', lazy='joined')
    type_id = sqlalchemy.Column(
        'show_type_id',
        sqlalchemy.ForeignKey('schedule.show_type.show_type_id'),
        nullable=False,
        server_default='1'
    )
    submitted_at = sqlalchemy.Column(
        'submitted',
        sqlalchemy.DateTime(timezone=True)
    )

    seasons = sqlalchemy.orm.relationship('Season')

    @classmethod
    def meta_sources(cls):
        """See 'lass.metadata.mixins.MetadataSubject.meta_sources'."""
        return [lass.metadata.query.own(with_default=True)]

    @classmethod
    def annotate(cls, shows):
        """Annotates a list of shows with their standard metadata and credits
        sets.

        Args:
            shows: A list of shows to annotate in-place.
        """
        cls.add_meta(shows, 'text', 'title', 'description', 'tags')
        cls.add_meta(shows, 'image', 'thumbnail_image', 'player_image')
        cls.add_credits(shows, with_byline_attr='byline')


class Term(lass.Base):
    # NB: Term is not in the schedule schema.
    __tablename__ = 'terms'
    query = lass.model_base.DBSession.query_property()

    id = sqlalchemy.Column(
        'termid',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )
    start = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))
    end = sqlalchemy.Column('finish', sqlalchemy.DateTime(timezone=True))
    name = sqlalchemy.Column('descr', sqlalchemy.String(length=10))

    @classmethod
    def of(cls, datetime):
        """Returns the term of the given datetime.

        If the date lies outside a term, the last active term is returned.
        This case can easily be distinguished by checking the returned term's
        'end' attribute.

        Args:
            datetime: An aware datetime for which a corresponding term is
                sought.  If None, the current time will be used.
                (Default: None.)

        Returns:
            The term on the date, or the last active term if none exists.
            Technically, this returns the last term to start before the date.
        """
        if datetime is None:
            datetime = lass.common.time.aware_now()

        return cls.query.filter(
            cls.start <= datetime
        ).order_by(
            sqlalchemy.desc(cls.start)
        ).first()


class Season(
    lass.metadata.mixins.MetadataSubject,
    lass.people.mixins.PersonSubmittable,
    ScheduleModel
):
    """A show season.

    Seasons map onto terms of scheduled timeslots for a show.
    """
    __tablename__ = 'show_season'
    query = lass.model_base.DBSession.query_property()

    id = lass.common.rdbms.infer_primary_key(__tablename__)

    show_id = sqlalchemy.Column(sqlalchemy.ForeignKey(Show.id))
    show = sqlalchemy.orm.relationship(Show, lazy='joined')

    term_id = sqlalchemy.Column('termid', sqlalchemy.ForeignKey(Term.id))
    term = sqlalchemy.orm.relationship(Term, lazy='joined')

    timeslots = sqlalchemy.orm.relationship('Timeslot')

    @classmethod
    def meta_sources(cls, meta_type):
        """See 'lass.metadata.mixins.MetadataSubject.meta_sources'."""
        return [lass.metadata.query.own(with_default=True)]


class BaseTimeslot(object):
    """The common level of functionality available on both data-model and
    pseudo-timeslots.
    """
    def __init__(self, start_time, duration):
        self.start_time = start_time
        self.duration = duration

    @property
    def end_time(self):
        """Returns the end time of the timeslot."""
        return self.start_time + self.duration

    @property
    def start_date(self):
        """Returns the start date (sans time) of the timeslot."""
        return self.start_time.date()


class Timeslot(
    lass.metadata.mixins.MetadataSubject,
    lass.people.mixins.Approvable,
    lass.people.mixins.Ownable,
    ScheduleModel,
    BaseTimeslot
):
    """A schedule timeslot."""
    __tablename__ = 'show_season_timeslot'
    query = lass.model_base.DBSession.query_property()

    id = lass.common.rdbms.infer_primary_key(__tablename__)

    season_id = sqlalchemy.Column(
        'show_season_id',
        sqlalchemy.ForeignKey(Season.id)
    )
    season = sqlalchemy.orm.relationship(Season, lazy='joined')

    start_time = sqlalchemy.Column(sqlalchemy.DateTime(timezone=True))
    duration = sqlalchemy.Column(sqlalchemy.Interval)

    tracklistings = sqlalchemy.orm.relationship(
        lass.music.models.TrackListing,
        backref='timeslot'
    )

    @property
    def tracklist(self):
        """Returns a list of tracks played during this timeslot.

        This runs one database query per usage.
        """
        in_library = lass.model_base.DBSession.query(
            lass.music.models.Track.title.label('track'),
            lass.music.models.Track.artist.label('artist'),
            lass.music.models.Record.title.label('record'),
            lass.music.models.TrackListing.timestart.label('played_at')
        ).select_from(
            lass.music.models.TrackListing
        ).join(
            lass.music.models.TrackListingLibraryTrack,
            lass.music.models.TrackListingLibraryTrack.track,
            lass.music.models.TrackListingLibraryTrack.record
        )

        out_library = lass.model_base.DBSession.query(
            lass.music.models.TrackListingCustomTrack.track.label('track'),
            lass.music.models.TrackListingCustomTrack.artist.label('artist'),
            lass.music.models.TrackListingCustomTrack.album.label('record'),
            lass.music.models.TrackListing.timestart.label('played_at')
        ).select_from(
            lass.music.models.TrackListing
        ).join(
            lass.music.models.TrackListingCustomTrack
        )

        return self.tracklist_filter(in_library).union(
            self.tracklist_filter(out_library)
        ).order_by(
            sqlalchemy.asc('played_at')
        ).all()

    def tracklist_filter(self, query):
        """Performs filtering for the tracklist mini-queries."""
        return query.filter(
            (lass.music.models.TrackListing.timeslotid == self.id) &
            (
                (lass.music.models.TrackListing.state_id == None) |
                (~lass.music.models.TrackListing.state_id.in_(['o', 'd']))
            )
        )


    @property
    def can_be_messaged(self):
        """Returns whether this timeslot can receive messages."""
        return self.season.show.type.can_be_messaged

    @classmethod
    def meta_sources(cls):
        """See 'lass.metadata.mixins.MetadataSubject.meta_sources'."""
        return [lass.metadata.query.own(with_default=True)]

    @classmethod
    def annotate(cls, timeslots):
        """Annotates timeslots with common metadata and credits information."""
        cls.add_meta(timeslots, 'text', 'title')

        # Grab, in bulk, the metadata for all the shows these timeslots come
        # from.  Make sure we can get back to the timeslots the shows belong
        # to, so keep lists associated with them (we'll see why later.)
        shows = {}
        for timeslot in timeslots:
            show = timeslot.season.show
            if show in shows:
                shows[show].append(timeslot)
            else:
                shows[show] = [timeslot]

        Show.annotate(list(shows.keys()))

        # NB: Maybe add season metadata into the mix too, if people start
        # giving seasons interesting names etc.  For now, shows and
        # timeslots are sufficient though.  ~Matt

        # Poor man's metadata inheritance.  This used to be automatic, but
        # doing it manually and explicitly saves a lot of complexity in the
        # metadata system itself.
        for show, show_timeslots in shows.items():
            for show_timeslot in show_timeslots:
                # This metadata is currently not handled at all by
                # timeslots, so copy it all over from the show verbatim.
                show_timeslot.image = show.image
                show_timeslot.byline = show.byline
                show_timeslot.credits = show.credits

                # For the text metadata, it'd be nice to merge show and
                # timeslot metadata.  Give timeslots precedence so any
                # custom episode metadata is pulled in first.
                for key, value in show.text.items():
                    if key in show_timeslot.text:
                        show_timeslot.text[key] += value
                    else:
                        show_timeslot.text[key] = value


class Message(lass.model_base.Base):
    """An entry in the SIS communication system."""
    __tablename__ = 'messages'
    __table_args__ = {'schema': 'sis2'}

    # TODO: add in sister tables.

    id = sqlalchemy.Column(
        'commid',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )

    timeslotid = sqlalchemy.Column(sqlalchemy.ForeignKey(Timeslot.id))
    timeslot = sqlalchemy.orm.relationship(Timeslot, lazy='joined')
    # Should be a foreign key to sis_commtype
    commtypeid = sqlalchemy.Column(sqlalchemy.Integer)
    sender = sqlalchemy.Column(sqlalchemy.String(64))
    date = sqlalchemy.DateTime(timezone=True)
    subject = sqlalchemy.Column(sqlalchemy.String(255))
    content = sqlalchemy.Column(sqlalchemy.Text)
    # Should be a foreign key to sis_status
    statusid = sqlalchemy.Column(sqlalchemy.Integer)
    comm_source = sqlalchemy.Column(sqlalchemy.String(15))
