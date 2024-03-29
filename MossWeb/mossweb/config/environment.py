"""Pylons environment configuration"""
import os

from mako.lookup import TemplateLookup
from pylons import config
from sqlalchemy import engine_from_config

import mossweb.lib.app_globals as app_globals
import mossweb.lib.helpers
from mossweb.config.routing import make_map
import mossweb.model as model

def load_environment(global_conf, app_conf):
    """Configure the Pylons environment via the ``pylons.config``
    object
    """
    # Pylons paths
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    paths = dict(root=root,
                 controllers=os.path.join(root, 'controllers'),
                 static_files=os.path.join(root, 'public'),
                 templates=[os.path.join(root, 'templates')])

    # Initialize config with the basic options
    config.init_app(global_conf, app_conf, package='mossweb', paths=paths)

    config['routes.map'] = make_map()
    config['pylons.app_globals'] = app_globals.Globals()
    config['pylons.h'] = mossweb.lib.helpers
    config['pylons.strict_c'] = True

    # Create the Mako TemplateLookup, with the default auto-escaping
    config['pylons.app_globals'].mako_lookup = TemplateLookup(
        directories=paths['templates'],
        module_directory=os.path.join(app_conf['cache_dir'], 'templates'),
        input_encoding='utf-8', output_encoding='utf-8',
        imports=['from webhelpers.html import escape'],
        default_filters=['escape'])
    
    # Setup the SQLAlchemy^W Elixir database engine
    engine = engine_from_config(config, 'sqlalchemy.')
    if model.elixir.options_defaults.get('autoload'):
        # Reflected tables
        model.elixir.bind = engine
        model.metadata.bind = engine
        model.elixir.setup_all()
    else:
        # Non-reflected tables
        model.init_model(engine)
    
    # CONFIGURATION OPTIONS HERE (note: all config options will override
    # any Pylons config options)
