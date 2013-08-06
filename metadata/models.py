"""Models for the metadata system.

In addition to these, the metadata system infers and uses per-model
database tables for retrieving metadata.

---

Copyright (c) 2013, University Radio York.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

* Redistributions of source code must retain the above copyright notice,
  this list of conditions and the following disclaimer.
* Redistributions in binary form must reproduce the above copyright
  notice, this list of conditions and the following disclaimer in the
  documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import sqlalchemy

import lass.common.mixins
import lass.metadata.mixins
import lass.model_base
import lass.people.mixins


class MetadataModel(lass.model_base.Base):
    """Base for all models living in the metadata schema."""
    __abstract__ = True
    __table_args__ = {'schema': 'metadata'}


class Key(MetadataModel, lass.common.mixins.Type):
    """A metadata key, which defines the semantics of a piece of
    metadata.
    """
    __tablename__ = 'metadata_key'

    id = sqlalchemy.Column(
        'metadata_key_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )
    allow_multiple = sqlalchemy.Column(
        sqlalchemy.Boolean,
        server_default='FALSE'
    )
    # Duration, in seconds, of any cache entries for metadata with this key.
    cache_duration = sqlalchemy.Column(
        sqlalchemy.Integer,
        server_default='300'
    )
    searchable = sqlalchemy.Column(
        sqlalchemy.Boolean,
        nullable=False,
        server_default='FALSE'
    )
    plural = sqlalchemy.Column(
        sqlalchemy.String(255)
    )


class Attachable(
    sqlalchemy.ext.declarative.AbstractConcreteBase,
    lass.model_base.Base,
    lass.common.mixins.Transient,
    lass.people.mixins.Ownable,
    lass.people.mixins.Approvable
):
    """Abstract base for any model that can be 'attached' to another model,
    thus creating a new model class and table specific to that model.

    Used primarily for two things: metadata, packages and credits.
    """
    __abstract__ = False

    @sqlalchemy.ext.declarative.declared_attr
    def id(cls):
        return sqlalchemy.Column(
            cls.primary_key_field,
            sqlalchemy.Integer,
            primary_key=True,
            nullable=False
        )

    @sqlalchemy.ext.declarative.declared_attr
    def subject_id(cls):
        return sqlalchemy.Column(
            cls.subject_id_field,
            sqlalchemy.ForeignKey(cls.subject_id_target)
        )

    @sqlalchemy.ext.declarative.declared_attr
    def subject(cls):
        return sqlalchemy.orm.relationship(
            cls.subject_target,
            backref=cls.backref
        )


class Item(Attachable):
    """Abstract model for an item of metadata."""
    __abstract__ = True

    @sqlalchemy.ext.declarative.declared_attr
    def key_id(cls):
        return sqlalchemy.Column(
            'metadata_key_id',
            sqlalchemy.Integer,
            sqlalchemy.ForeignKey(Key.id)
        )

    @sqlalchemy.ext.declarative.declared_attr
    def key(cls):
        return sqlalchemy.orm.relationship(Key)


class Text(Item):
    """Abstract model for an item of textual metadata."""
    __abstract__ = True

    value = sqlalchemy.Column('metadata_value', sqlalchemy.Text)
    backref = 'text_entries'


class Image(Item):
    """Abstract model for an item of image metadata."""
    __abstract__ = True

    value = sqlalchemy.Column('metadata_value', sqlalchemy.String(255))
    backref = 'image_entries'


# NB: Package is technically a metadata subject, but do NOT add
# 'mixins.MetadataSubject' as this would introduce a cyclic dependency.
class Package(
    lass.model_base.Base,
    lass.common.mixins.Type
):
    """A 'package' is an object that can be applied to an
    object to provide an overridable, default set of metadata.
    """
    __tablename__ = 'package'
    __table_args__ = {'schema': 'metadata'}

    id = sqlalchemy.Column(
        'package_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )

    # From Type: name, description
    weight = sqlalchemy.Column('weight', sqlalchemy.Integer)


class PackageAttachable(MetadataModel):
    """Base class for all models defining an attachable bound to
    packages."""
    __abstract__ = True
    __mapper_args__ = {'polymorphic_identity': 'package', 'concrete': True}

    subject_id_field = 'package_id'
    subject_id_target = Package.id
    subject_target = Package


class PackageText(PackageAttachable, Text):
    __tablename__ = 'package_text_metadata'
    primary_key_field = 'package_text_metadata_id'


class PackageImage(PackageAttachable, Image):
    __tablename__ = 'package_image_metadata'
    primary_key_field = 'package_image_metadata_id'


class PackageEntry(Attachable):
    """An abstract model representing an entry in the package system.

    Use 'PackageEntry.attach(Model)' to generate a concrete entry model for that
    model.
    """
    __abstract__ = True
    backref = 'podcast_entries'

    @sqlalchemy.ext.declarative.declared_attr
    def package_id(cls):
        return sqlalchemy.Column(sqlalchemy.ForeignKey(Package.id))

    @sqlalchemy.ext.declarative.declared_attr
    def package(cls):
        return sqlalchemy.orm.relationship(Package)
