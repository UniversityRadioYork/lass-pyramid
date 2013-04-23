import sqlalchemy

from .. import Base
import lass.metadata.mixins
import lass.people.mixins


class Show(
    Base,
    lass.metadata.mixins.MetadataSubject,
    lass.people.mixins.PersonSubmittable
):
    __tablename__ = 'show'
    __table_args__ = {'schema': 'schedule'}

    # Table override (remove if/when 'show_metadata' is moved)
    meta_tables = {'text': 'show_metadata'}

    id = sqlalchemy.Column(
        'show_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )
    type = sqlalchemy.Column(
        'show_type_id',
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('schedule.show_type.show_type_id'),
        nullable=False,
        server_default='1',
    )
    submitted_at = sqlalchemy.Column(
        'submitted',
        sqlalchemy.DateTime(timezone=True)
    )

    @property
    def date(self):
        return self.submitted_at
