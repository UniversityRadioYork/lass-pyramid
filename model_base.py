# Please don't import anything from lass., to avoid circular dependencies
import sqlalchemy.ext.declarative
import sqlalchemy.orm
import zope.sqlalchemy


DBSession = sqlalchemy.orm.scoped_session(
    sqlalchemy.orm.sessionmaker(
        extension=zope.sqlalchemy.ZopeTransactionExtension()
    )
)


Base = sqlalchemy.ext.declarative.declarative_base()


class PublicModel(Base):
    """Base class for models in the public schema."""
    __abstract__ = True
    __table_args__ = {'schema': 'public'}
