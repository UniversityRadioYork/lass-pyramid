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
