import cgi

from paste.urlparser import PkgResourcesParser
from pylons import request, config
from pylons.controllers.util import forward
from pylons.middleware import error_document_template
from webhelpers.html.builder import literal

from pylons import tmpl_context as c
from mossweb.lib.base import render
from mossweb.lib import helpers as h
from turbomail import Message
from pylons.controllers.util import abort, redirect_to

from mossweb.lib.base import BaseController

class ErrorController(BaseController):

    """Generates error documents as and when they are required.

    The ErrorDocuments middleware forwards to ErrorController when error
    related status codes are returned from the application.

    This behaviour can be altered by changing the parameters to the
    ErrorDocuments middleware in your config/middleware.py file.

    """

#    def document(self):
#        """Render the error document"""
#        resp = request.environ.get('pylons.original_response')
#        content = literal(resp.body) or cgi.escape(request.GET.get('message', ''))
#        page = error_document_template % \
#            dict(prefix=request.environ.get('SCRIPT_NAME', ''),
#                 code=cgi.escape(request.GET.get('code', str(resp.status_int))),
#                 message=content)
#        return page
    def document(self):
        """Render the error document"""
        resp = request.environ.get('pylons.original_response')
        code = cgi.escape(request.GET.get('code', ''))
        content = cgi.escape(request.GET.get('message', ''))
        if resp:
            content = literal(resp.status)
            code = code or cgi.escape(str(resp.status_int))
        if not code:
            raise Exception('No status code was found')
        c.code = code
        c.message = content
        return render('/derived/error/error.html')


    def img(self, id):
        """Serve Pylons' stock images"""
        return self._serve_file('/'.join(['media/img', id]))

    def style(self, id):
        """Serve Pylons' stock stylesheets"""
        return self._serve_file('/'.join(['media/style', id]))

    def _serve_file(self, path):
        """Call Paste's FileApp (a WSGI application) to serve the file
        at the specified path
        """
        request.environ['PATH_INFO'] = '/%s' % path
        return forward(PkgResourcesParser('pylons', 'pylons'))
    
    def feedback(self):
        user = h.get_user(request.environ)
        from_addr = config['error_email_from']
        suffix = config['email_suffix']
        to_addr = "cemeyer2@illinois.edu"
        subject = "CoMoTo error feedback from "+user.name      
        body = request.params['feedback']
        body += "\n\n"
        body += "revision reporting problem: "+c.revision
        if body is not None:
            message = Message(from_addr, to_addr, subject)
            message.plain = body
            message.send()
        
        redirect_to(controller='login', action='index')
