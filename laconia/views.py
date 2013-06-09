import importlib

import dateutil
import pyramid

import lass.model_base

def model_from_matchdict(md):
    """Extracts a model from a matchdict containing keys 'package' and
    'model'.

    The model's fully qualified name is thus 'lass.(package).(MODEL)' where
    'package' is lowercased and 'model' is capitalised.
    """
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
    return model


def items_from_matchdict(md, model):
    """Retrieves items from 'model' as referenced by 'ids' in the matchdict.

    'ids' is a '+'-delimited string listing the primary keys to retrieve.
    """
    subject_keys = [int(key) for key in md['ids'].split('+') if key]
    items = lass.model_base.DBSession.query(model).filter(
        model.id.in_(subject_keys)
    )
    if not items:
        raise pyramid.exceptions.NotFound(
            'No such {}(s).'.format(md['model'])
        )
    return items


def date_from_matchdict(md):
    """Retrieves a date from the matchdict at key 'date'.

    If 'date' is 'now', then None is retrieved, in the hopes that this will be
    replaced with the current datetime further down.
    """
    return (
        None
        if md['date'].lower() == 'now'
        else dateutil.parser.parse(md['date'])
    )


@pyramid.view.view_config(
    route_name='laconia-credits',
    renderer='json'
)
def credits(request):
    """A view that outputs the result of a credit query."""
    md = request.matchdict
    model = model_from_matchdict(md)
    items = items_from_matchdict(md, model)
    date = date_from_matchdict(md)
    return model.bulk_credits(
        items,
        *(s for s in md['types'].split('+') if s),
        date=date
    )


@pyramid.view.view_config(
    route_name='laconia-metadata',
    renderer='json'
)
def metadata(request):
    """A view that outputs the result of a metadata query."""
    md = request.matchdict
    model = model_from_matchdict(md)
    items = items_from_matchdict(md, model)
    date = date_from_matchdict(md)

    return model.bulk_meta(
        items,
        md['type'],
        *(s for s in md['keys'].split('+') if s),
        date=date
    )
