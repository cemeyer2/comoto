import os
os.environ['PYTHON_EGG_CACHE'] = '/usr/dcs/www/pylons/MossWeb/egg-cache'
# Load the Pylons application
from paste.deploy import loadapp
application = loadapp('config:/usr/dcs/www/pylons/MossWeb/production.ini')