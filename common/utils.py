"""Miscellaneous utilities."""

def annotate(items, annotations, attribute_name):
    """Annotates each item in 'items' with corresponding data in 'annotations'.

    Args:
        items: Objects with an attribute 'id' that corresponds to the keys in
            'annotations'.
        annotations: A dict mapping item IDs to annotations.
        attribute_name: The name of the attribute to create or update on each
            item in 'items' with the annotations.
    """
    for item in items:
        if not hasattr(item, attribute_name):
            setattr(item, attribute_name, dict())
        getattr(item, attribute_name).update(annotations[item.id])
