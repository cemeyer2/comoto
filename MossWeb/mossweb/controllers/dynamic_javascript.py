import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from mossweb.lib.base import BaseController, render

log = logging.getLogger(__name__)

class DynamicJavascriptController(BaseController):

    def facebox(self):
        response.content_type = "text/javascript"
        return render("/js/facebox.js")

    def facebox2(self):
        response.content_type = "text/javascript"
        return render("/js/facebox2.js.min.js")
