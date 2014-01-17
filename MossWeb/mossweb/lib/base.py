"""The base Controller API

Provides the BaseController class for subclassing.
"""
import logging
from pylons.controllers import WSGIController
from pylons.templating import render_mako as render
from pylons import config
from mossweb import model
from pylons import request, response, session, tmpl_context as c
import subprocess, os
from mossweb.lib import helpers as h

log = logging.getLogger(__name__)


class BaseController(WSGIController):
    
    def __call__(self, environ, start_response):
        """Invoke the Controller"""
        # WSGIController.__call__ dispatches to the Controller method
        # the request is routed to. This routing information is
        # available in environ['pylons.routes_dict']

        # Insert any code to be run per request here.
        # hg parents --template="r{rev} {date|date} by {author}\n"
        hg_args = ['hg', 'parents', '--template="r{rev} {date|date} by {author}\n"']
        hg_process = subprocess.Popen(hg_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=os.path.dirname(__file__))
        c.revision = hg_process.stdout.readline().strip()[1:]
        if request.environ['HTTP_HOST'].startswith("comoto") and h.get_user(request.environ).superuser: #we are running on the production server and we are a superuser
            hg_args = ['hg', 'incoming', '--template="{rev}\n"']
            hg_process = subprocess.Popen(hg_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=os.path.dirname(__file__))
            incoming_changesets = -2 #start with -4 because of extra lines printed
            while True:
                output = hg_process.stdout.readline()
		if len(output) > 2:
               	    incoming_changesets+=1
                if output.startswith("no"):
                    incoming_changesets = 0
                    break
                if output == '' or hg_process.poll() != None:
                    break
            c.incoming_changesets = incoming_changesets
        try:
            return WSGIController.__call__(self, environ, start_response)
        finally:
            model.Session.remove()
    
