"""Models for the metadata system.

In addition to these, the metadata system infers and uses per-model database
tables for retrieving metadata.  See 'metadata.rdbms' for more information.
"""

import sqlalchemy

import lass.common.mixins
import lass.model_base
import lass.people


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


# NB: Package is technically a metadata subject, but do NOT add
# 'mixins.MetadataSubject' as this would introduce a cyclic dependency.
class Package(
    lass.Base,
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

# There is also a table 'xyz_package_entry' for every MetadataSubject xyz that
# uses packages as a metadata source.
