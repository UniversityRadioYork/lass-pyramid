"""Functions for retrieving LASS configuration from config files."""

import pyramid
import yaml


def from_yaml(path):
    """Reads in a YAML configuration file, given its path.
    
    Args:
        path: The path of the configuration file, relative to the config
            directory and without the '.yml' prefix.  For example,
            'sitewide/website' will retrieve the main website file.

    Returns:
        The processed contents of the configuration file (usually a dict).
    """
    asset = 'config:{}.yml'.format(path)
    full_path = pyramid.path.AssetResolver().resolve(asset).abspath()
    
    with open(full_path) as yaml_file:
        result = yaml.load(yaml_file)

    return result
