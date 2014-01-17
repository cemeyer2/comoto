'''
Created on Mar 31, 2010

@author: chuck
'''

from decorator import decorator
from pylons import request
import pylons
import logging
from mossweb.lib import helpers as h
from pylons.controllers.util import abort
from mossweb.model.model import *

log = logging.getLogger(__name__)

def require_superuser():
    def wrapper(func, self, *args, **kw):
        user = h.get_user(request.environ)
        if user.superuser:
            return func(self, *args, **kw)
        abort(403)
    return decorator(wrapper)

def require_enabled_user():
    def wrapper(func, self, *args, **kw):
        user = h.get_user(request.environ)
        if user.enabled:
            return func(self, *args, **kw)
        abort(403)
    return decorator(wrapper)