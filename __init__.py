from pyramid.config import Configurator
from sqlalchemy import engine_from_config

import lass.model_base

#from . import (
#    common,
#    people,
#    model_base
#)


def main(_, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    lass.model_base.DBSession.configure(bind=engine)
    lass.model_base.Base.metadata.bind = engine
    config = Configurator(settings=settings)
    config.include('pyramid_zcml')
    config.load_zcml('config.global:configure.zcml')
    return config.make_wsgi_app()
