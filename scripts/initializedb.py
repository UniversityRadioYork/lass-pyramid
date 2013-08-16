import os
import sys
import pyramid.paster
import sqlalchemy

import lass.model_base


def usage(full_cmd):
    cmd = os.path.basename(full_cmd)
    print(
        'usage: {0} <config_uri>\n'
        '(example: "{0} development.ini")'.format(cmd)
    )
    sys.exit(1)


def main(argv=sys.argv):
    full_cmd, *rest = argv
    try:
        (config_uri, ) = rest
    except ValueError:
        usage(full_cmd)

    # Don't forget to add any new model modules here
    import lass.credits.models
    import lass.metadata.models
    import lass.music.models
    import lass.people.models
    import lass.schedule.models
    import lass.uryplayer.models

    pyramid.paster.setup_logging(config_uri)
    settings = pyramid.paster.get_appsettings(config_uri)
    engine = sqlalchemy.engine_from_config(settings, 'sqlalchemy.')
    lass.model_base.DBSession.configure(bind=engine)

    # Don't forget to add any new schemata here
    schemata = set()
    for table in lass.model_base.Base.metadata.sorted_tables:
        if table.schema:
            schemata.add(table.schema)

    for schema in schemata:
        try:
            engine.execute(sqlalchemy.schema.CreateSchema(schema))
        except sqlalchemy.exc.ProgrammingError:
            # Assume this means the schema already exists
            pass

    lass.model_base.Base.metadata.create_all(engine)
