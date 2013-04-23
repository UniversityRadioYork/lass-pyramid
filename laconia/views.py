import importlib

import dateutil
import pyramid

import lass.model_base
import lass.schedule.models


@pyramid.view.view_config(
    route_name='laconia-metadata',
    renderer='json'
)
def metadata(request):
    """A view that outputs the result of a metadata query."""
    md = request.matchdict

    package_name = '.'.join(('lass', md['package'], 'models'))
    try:
        package = importlib.import_module(package_name)
    except ImportError:
        raise pyramid.exceptions.NotFound(
            '{} is not a valid package.'.format(package_name)
        )

    model_name = md['model'].capitalize()
    try:
        model = getattr(package, model_name)
    except AttributeError:
        raise pyramid.exceptions.NotFound(
            '{}.{} is not a valid model.'.format(package_name, model_name)
        )
    subject_keys = [int(key) for key in md['id'].split('+') if key]
    items = lass.model_base.DBSession.query(model).filter(
        model.id.in_(subject_keys)
    )
    if not items:
        raise pyramid.exceptions.NotFound(
            'No such {}(s).'.format(md['model'])
        )
    date = (
        None
        if md['date'].lower() == 'now'
        else dateutil.parser.parse(md['date'])
    )
    return model.bulk_meta(
        items,
        md['type'],
        *(s for s in md['keys'].split('+') if s),
        date=date
    )
