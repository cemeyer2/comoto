import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from mossweb.lib.base import BaseController, render
from mossweb.lib import helpers as h

from pylons import config

from turbomail import Message
from pylons.controllers.xmlrpc import XMLRPCController
from mossweb.controllers.api import ApiController

log = logging.getLogger(__name__)

class AboutController(BaseController):

    def index(self):
        return render("/derived/about/index.html")

    def api(self):
        methods = XMLRPCController.__dict__["system_listMethods"].__call__(ApiController())
        c.methods = methods
        return render("/derived/about/api.html")
    
    def pformat(self):
        if not request.params.has_key("data"):
            return "";
        data = request.params['data']
        data = data.replace("true", "True")
        data = data.replace("false", "False")
        try:
            from pprint import pformat
            return pformat(eval(data,{},{})) #eval with empty locals and globals for safety
        except:
            return data
    
    def feedback(self):
        user = h.get_user(request.environ)
        from_addr = config['error_email_from']
        suffix = config['email_suffix']
        to_addr = "cemeyer2@illinois.edu"
        subject = "CoMoTo feedback from "+user.name      
        body = request.params['feedback']
        body += "\n\n"
        body += "revision reporting problem: "+c.revision
        if body is not None:
            message = Message(from_addr, to_addr, subject)
            message.plain = body
            message.send()
            session['flash'] = "Feedback Sent"
            session.save()
        
        redirect_to(controller='about', action='comoto')
