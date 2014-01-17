"""The application's model objects"""
import elixir
from mossweb.model import meta

Session = elixir.session = meta.Session
# Uncomment if using reflected tables
# elixir.options_defaults.update({'autoload': True})
elixir.options_defaults.update({'shortnames':True})
metadata = elixir.metadata

# this will be called in config/environment.py
# if not using reflected tables
def init_model(engine):
    """Call me before using any of the tables or classes in the model"""
    meta.Session.configure(bind=engine)
    metadata.bind = engine

# Delay the setup if using reflected tables
if elixir.options_defaults.get('autoload', False) \
    and not metadata.is_bound():
    elixir.delay_setup = True

# # import other entities here, e.g.
# from mossweb.model.blog import BlogEntry, BlogComment

from mossweb.model.model import User

# Finally, call elixir to set up the tables.
# but not if using reflected tables
if not elixir.options_defaults.get('autoload', False):
    elixir.setup_all()