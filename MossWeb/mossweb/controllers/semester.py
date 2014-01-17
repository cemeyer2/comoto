import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from mossweb.lib.base import BaseController, render
from mossweb.lib.decorators import require_superuser

from mossweb.model.model import Semester
from mossweb.model import Session
from mossweb.lib import helpers as h
from mossweb.lib.decorators import require_enabled_user

log = logging.getLogger(__name__)

class SemesterController(BaseController):

    @require_enabled_user()
    def __before__(self, controller, action):
        pass

    @require_superuser()
    def manage(self):
        c.semesters = Semester.query.all()
        c.semesters.sort()
        return render("/derived/semester/manage.html")
    
    @require_superuser()
    def new_semester(self):
        season = request.params['season']
        year = int(request.params['year'])
        if Semester.query.filter_by(year=year, season=season).count() == 0:
            semester = Semester()
            semester.season = request.params['season']
            semester.year = int(request.params['year'])
            Session.commit()
        redirect_to(controller='semester', action='manage')