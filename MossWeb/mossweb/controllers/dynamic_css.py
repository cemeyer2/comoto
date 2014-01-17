import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from mossweb.lib.base import BaseController, render

log = logging.getLogger(__name__)

class DynamicCssController(BaseController):

    def facebox(self):
        response.content_type = "text/css"
        return render("/css/facebox.css")
    
    def cluetip(self):
        response.content_type = "text/css"
        return render("/css/jquery.cluetip.css")
