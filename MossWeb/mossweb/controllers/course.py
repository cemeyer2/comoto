import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from mossweb.lib.base import BaseController, render
from mossweb.lib import helpers as h
from mossweb.lib import ldap_helpers as lh
from mossweb.model.model import Course, Offering, Semester, User, SolutionSemester, BaseSemester
from mossweb.model import Session
import formencode
from formencode import htmlfill
from pylons.decorators import validate
from pylons.decorators.rest import restrict
from mossweb.lib.decorators import require_superuser, require_enabled_user
from mossweb.lib.access import check_course_access
from mossweb.lib.ldap_helpers import get_all_courses
import re

log = logging.getLogger(__name__)

class UniqueCourse(formencode.validators.FancyValidator):
    def _to_python(self, value, state):
        # Check we have a valid string first
        value = formencode.validators.String(max=20).to_python(value, state)
        # Check that tags are only letters, numbers, and the space character
        result = re.compile("[^a-zA-Z0-9 ]").search(value)
        if result:
            raise formencode.Invalid("Course names can only contain letters, numbers and spaces", value, state)
        # Ensure the tag is unique
        course_q = Course.query.filter_by(name=value)
        if request.urlvars['action'] == 'save':
            # Ignore the existing name when performing the check
            course_q = course_q.filter(Course.id != int(request.urlvars['id']))
        first_course = course_q.first()
        if first_course is not None:
            raise formencode.Invalid("This course name already exists", value, state)
        return value

class NewCourseForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    name = UniqueCourse(not_empty=True)

class CourseController(BaseController):

    @require_enabled_user()
    def __before__(self, controller, action):
        pass

    @require_superuser()
    def admin(self):
        c.user = h.get_user(request.environ)
        c.courses = Course.query.all()
        for course in c.courses:
            course.users.sort()
        all_courses = get_all_courses()
        textExp = re.compile(r'(\S*)\s*(\d*).*')
        for course in c.courses:
            (dept, num) = textExp.match(course.name).group(1, 2)
            if all_courses.has_key(dept):
                if int(num) in all_courses[dept]:
                    all_courses[dept].remove(int(num))
        c.all_courses = all_courses
        return render("/derived/course/list.html")
        
    @restrict('POST')
    @require_superuser()
    def new(self):
        if not request.params.has_key("department") or not request.params.has_key("number"):
            abort(404)
        name = request.params['department'] + " "+ request.params['number']
        user = h.get_user(request.environ)
        if len(Course.query.filter_by(name=name).all()) > 0:
            return redirect_to(h.url_for(controller='course', action='admin', id=None))
        course = Course(name=name)
        for su in User.query.filter_by(superuser=True).all():
            su.courses.append(course)
        soln = SolutionSemester.query.all()[0]
        solnoffering = Offering(course=course, semester=soln)
        base = BaseSemester.query.all()[0]
        baseoffering = Offering(course=course, semester=base)
        Session.commit()
        return redirect_to(h.url_for(controller='course', action='admin', id=None))
    
    @require_superuser()
    def manage_course(self, id=None):
        if id is None:
            abort(404)
        c.course = h.get_object_or_404(Course, id=id)
        c.course.users.sort()
        c.available_users = filter(lambda x: x not in c.course.users, User.query.all())
        c.available_users.sort()
        course_staff = lh.get_course_staff(c.course)
        for user in c.course.users:
            if user in course_staff:
                course_staff.remove(user)
        course_staff.sort()
        c.potential_users = course_staff
        lh.populate_user_from_active_directory(User.query.all())
        lh.populate_user_from_active_directory(c.potential_users)
        Session.commit()
        return render("/derived/course/manage_course.html")
    
    @require_superuser()
    def remove_course(self, id=None):
        if id is None:
            abort(404)
        course = h.get_object_or_404(Course, id=id)
        Session.delete(course)
        Session.commit()
        return redirect_to(h.url_for(controller='course', action='admin'))
    
    @require_superuser()
    def remove_user(self, id=None):
        if id is None:
            abort(404)
        course = h.get_object_or_404(Course, id=id)
        user_id = request.params['user_id']
        user = h.get_object_or_404(User, id=user_id)
        log.debug(str(user))
        user.courses.remove(course)
        Session.commit()
        return redirect_to( h.url_for(controller='course', action='manage_course', id=course.id))
    
    @require_superuser()
    def add_user(self, id=None):
        if id is None:
            abort(404)
        course = h.get_object_or_404(Course, id=id)
        user_id = request.params['user_id']
        user = h.get_object_or_404(User, id=user_id)
        user.courses.append(course)
        if not user.enabled:
            user.enabled = True
            h.send_user_enabled_email(user)
        Session.commit()
        return redirect_to(h.url_for(controller='course', action='manage_course', id=course.id))
            
    
    def manage_offerings(self, id=None):
        if id is None:
            abort(404)
        check_course_access(id)
        course = h.get_object_or_404(Course, id=id)
        c.course = course
        semesters = Semester.query.all()
        
        def is_available(semester):
            for offering in course.offerings:
                if offering.semester.id == semester.id:
                    return False
            return True
        
        c.semesters = filter(is_available, semesters)
        c.semesters.sort()
        return render("/derived/course/manage_offerings.html")
    
    def new_offering(self, id=None):
        if id is None:
            abort(404)
        course = h.get_object_or_404(Course, id=id)
        check_course_access(id)
        if not request.params.has_key('semester'):
            abort(404)
        semester_id = request.params['semester']
        semester = h.get_object_or_404(Semester, id=semester_id)
        offering = Offering(course=course, semester=semester)
        Session.commit()
        return redirect_to(h.url_for(controller='course', action='manage_offerings', id=course.id))        
        

