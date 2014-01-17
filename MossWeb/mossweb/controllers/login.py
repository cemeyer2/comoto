import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from mossweb.model.model import User, Semester
from mossweb.lib.base import BaseController, render
from mossweb.lib import helpers as h
from sqlalchemy.orm.exc import NoResultFound
from mossweb.model import Session


log = logging.getLogger(__name__)

class LoginController(BaseController):

    def index(self):
        user = h.get_user(request.environ)
        c.user = user
        courses = user.courses
        courses.sort()
        c.courses = courses
        Session.commit()
        if user.enabled:
            return render("/derived/main.html")
        else:
            return render("/derived/login/user_not_in_system.html")

        
