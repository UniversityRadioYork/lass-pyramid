"""Models for the metadata system.

In addition to these, the metadata system infers and uses per-model database
tables for retrieving metadata.  See 'metadata.rdbms' for more information.
"""

import sqlalchemy

import lass.common.mixins
import lass.model_base
import lass.people.mixins


def package_foreign_key(*args, **keywords):
    """Wrapper around 'Column' for defining a foreign key to a Package."""
    return lass.common.rdbms.foreign_key_from(Package.id, *args, **keywords)


class Key(lass.model_base.Base, lass.common.mixins.Type):
    """A metadata key, which defines the semantics of a piece of
    metadata.
    """
    __tablename__ = 'metadata_key'
    __table_args__ = {'schema': 'metadata'}

    id = lass.common.rdbms.infer_primary_key(__tablename__)
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
    """
    __abstract__ = False
    pass


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

    value = sqlalchemy.Column(
        'metadata_value',
        sqlalchemy.Text
    )


class Image(Item):
    """Abstract model for an item of image metadata."""
    __abstract__ = True

    value = sqlalchemy.Column(
        'metadata_value',
        sqlalchemy.String(255)
    )


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

    id = lass.common.rdbms.infer_primary_key(__tablename__)

    # From Type: name, description
    weight = sqlalchemy.Column('weight', sqlalchemy.Integer)


class PackageText(Text):
    __tablename__ = 'package_text_metadata'
    __table_args__ = {'schema': 'metadata'}
    __mapper_args__ = {'polymorphic_identity': 'package', 'concrete': True}
    id = sqlalchemy.Column(
        'package_text_metadata_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )
    subject_id = sqlalchemy.Column(
        'package_id',
        sqlalchemy.ForeignKey(Package.id)
    )
    subject = sqlalchemy.orm.relationship(Package, backref='text_entries')


class PackageImage(Image):
    __tablename__ = 'package_image_metadata'
    __table_args__ = {'schema': 'metadata'}
    __mapper_args__ = {'polymorphic_identity': 'package', 'concrete': True}
    id = sqlalchemy.Column(
        'package_image_metadata_id',
        sqlalchemy.Integer,
        primary_key=True,
        nullable=False
    )
    subject_id = sqlalchemy.Column(
        'package_id',
        sqlalchemy.ForeignKey(Package.id)
    )
    subject = sqlalchemy.orm.relationship(Package, backref='image_entries')


class PackageEntry(Attachable):
    """An abstract model representing an entry in the package system.

    Use 'PackageEntry.attach(Model)' to generate a concrete entry model for that
    model.
    """
    __abstract__ = True

    @sqlalchemy.ext.declarative.declared_attr
    def package_id(cls):
        return sqlalchemy.Column(sqlalchemy.ForeignKey(Package.id))

    @sqlalchemy.ext.declarative.declared_attr
    def package(cls):
        return sqlalchemy.orm.relationship(Package)
