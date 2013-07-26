import sqlalchemy


class Approvable(object):
    """Mixin for items that must be approved before becoming usable."""
    @sqlalchemy.ext.declarative.declared_attr
    def approver_id(cls):
        return sqlalchemy.Column(
            'approvedid',
            sqlalchemy.ForeignKey('member.memberid'),
            nullable=False
        )

    @sqlalchemy.ext.declarative.declared_attr
    def approver(cls):
        return sqlalchemy.orm.relationship(
            'Person',
            primaryjoin='Person.id == {}.approver_id'.format(cls.__name__)
        )


class Ownable(object):
    """Mixins for models that are ownable by people."""
    @sqlalchemy.ext.declarative.declared_attr
    def owner_id(cls):
        return sqlalchemy.Column(
            'memberid',
            sqlalchemy.ForeignKey('member.memberid'),
            nullable=False
        )

    @sqlalchemy.ext.declarative.declared_attr
    def owner(cls):
        return sqlalchemy.orm.relationship(
            'Person',
            primaryjoin='Person.id == {}.owner_id'.format(cls.__name__)
        )
