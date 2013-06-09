from pyramid.config import Configurator
from sqlalchemy import engine_from_config

from .model_base import (
    DBSession,
    Base,
)

from . import (
    common
)


def main(_, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('pyramid_zcml')
    config.load_zcml('config.global:configure.zcml')
    return config.make_wsgi_app()
