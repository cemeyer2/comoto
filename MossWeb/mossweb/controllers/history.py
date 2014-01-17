import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from mossweb.lib.base import BaseController, render

log = logging.getLogger(__name__)

from mossweb.model.model import *
from mossweb.lib import helpers as h
from mossweb.lib import ldap_helpers as lh
from mossweb.lib.history_helpers import filter_moss_matches_to_limit_per_assignment
from mossweb.lib.access import check_student_access
from mossweb.lib.decorators import require_enabled_user
from mossweb.lib.phclient import PHClient

from sqlalchemy import or_

class HistoryController(BaseController):

    @require_enabled_user()
    def __before__(self, controller, action):
        pass

    def index(self):
        redirect_to(controller="history", action="search")
    
    def filter(self, id):
        like = id+"%"
        students = Student.query.filter(Student.netid.like(like) | Student.displayName.like(like)).all()
        retval = "<ul>"
        user = h.get_user(request.environ)
        for student in students:
            show = False
            for offering in student.offerings:
                if offering.course in user.courses or user.superuser:
                    show = True
            if show:
                if student.displayName is not None:
                    retval += "<li><a href='"+h.url_for(controller="history", action="view", id=student.netid)+"'>"+student.netid+"</a> - "+student.displayName+" </li>"
                else:
                    retval += "<li><a href='"+h.url_for(controller="history", action="view", id=student.netid)+"'>"+student.netid+"</a></li>"
        retval += "</ul>"
        return retval
    
    def search(self):
        user = h.get_user(request.environ)
        c.user = user
        c.link_base = h.url_for(controller="history", action="view")
        return render("/derived/history/search.html")
    
    def view(self, id):
        if id is None:
            abort(404)
        user = h.get_user(request.environ)
        student = h.get_object_or_404(Student, netid=id)
        check_student_access(student)
        c.student = student
        lh.populate_student_from_active_directory(student)
        submissions = filter(lambda submission: submission.offering.course in user.courses, student.submissions)
        c.submissions = submissions
        c.ph_data = lh.get_student_directory_info(student)
        return render("/derived/history/view.html")
    
    def get_matches(self, id):
        if id is None:
            abort(404)
        user = h.get_user(request.environ)
        student = h.get_object_or_404(Student, netid=id)
        check_student_access(student)
        minimum_match_score = 0
        if request.params.has_key("minimum_match_score"):
            minimum_match_score = int(request.params['minimum_match_score'])
        max_matches_per_assignment = -1
        if request.params.has_key("max_matches_per_assignment"):
            max_matches_per_assignment = int(request.params['max_matches_per_assignment'])
        submissions = filter(lambda submission: submission.offering.course in user.courses, student.submissions)
        c.submissions = submissions
        matches = []
        #unfortunately, the query below is not yet supported by sqlalchemy
        #matches = MossMatch.query.filter(or_(MossMatch.submission1.id.in_(sub_ids), MossMatch.submission2.id.in_(sub_ids))).all()
        #for sub in submissions:
        #    temp = MossMatch.query.filter(or_(MossMatch.submission1 == sub, MossMatch.submission2 == sub)).all()
        #    matches.extend(temp)
        ids = [s.id for s in submissions]
        matches.extend(MossMatch.query.join(MossMatch.submission1).filter(Submission.id.in_(ids)).all())
        matches.extend(MossMatch.query.join(MossMatch.submission2).filter(Submission.id.in_(ids)).all())
        matches = filter(lambda match: match.mossAnalysis.analysis.assignment.course in user.courses, matches)
        matches.sort()
        matches.reverse()
        matches = h.filter_moss_matches_to_minimum_score(matches, minimum_match_score)
        matches = filter_moss_matches_to_limit_per_assignment(matches, max_matches_per_assignment)
        def comparator(match1, match2):
            t1 = match1.mossAnalysis.analysis.timestamp
            t2 = match2.mossAnalysis.analysis.timestamp
            t_cmp = cmp(t1,t2)
            if t_cmp == 0:
                return cmp(match1, match2)
            else:
                return t_cmp
        matches = sorted(matches, cmp=comparator, reverse=True)
        c.matches = matches
        c.student = student
        return render("/derived/history/matches_ajax.html")
        