import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from mossweb.lib.base import BaseController, render
from mossweb.lib.decorators import require_superuser, require_enabled_user

from mossweb.model.model import User, Course
from mossweb.model import Session
from mossweb.lib import helpers as h
from mossweb.lib import ldap_helpers as lh
from pylons import config
import datetime
from turbomail import Message
from mossweb.lib.ldap_helpers import populate_user_from_active_directory

log = logging.getLogger(__name__)

class UsersController(BaseController):

    @require_enabled_user()
    def __before__(self, controller, action):
        pass

    @require_superuser()
    def manage(self):
        c.users = User.query.filter_by(enabled=True).all()
        c.users.sort()
        c.pending_users = User.query.filter_by(enabled=False).all()
        c.pending_users.sort()
        lh.populate_user_from_active_directory(c.pending_users)
        lh.populate_user_from_active_directory(c.users)
        
        return render("/derived/users/list.html")
    
    @require_superuser()
    def remove_user(self, id=None):
        if id is None:
            abort(404)
        user = h.get_object_or_404(User, id=id)
        user.courses = []
        Session.delete(user)
        Session.commit()
        response.status_int = 302
        response.headers['location'] = h.url_for(controller='users', action='manage')
        return "Moved temporarily"
    
    @require_superuser()
    def new_user(self):
        name = request.params['name']
        superuser = bool(int(request.params['superuser']))
        user = User(name=name, superuser=superuser)
        if user.superuser:
            user.courses = Course.query.all()
        populate_user_from_active_directory(user)
        Session.commit()
        response.status_int = 302
        response.headers['location'] = h.url_for(controller='users', action='manage')
        return "Moved temporarily"
    
    @require_superuser()
    def manage_user(self, id=None):
        if id is None:
            abort(404)
        c.user = h.get_object_or_404(User, id=id)
        c.available_courses = filter(lambda x: x not in c.user.courses, Course.query.all())
        return render("/derived/users/manage_user.html")
    
    @require_superuser()
    def edit_superuser(self):
        id = request.params['user_id']
        if id is None:
            abort(404)
        user = h.get_object_or_404(User, id=id)
        if request.params.has_key('superuser'):
            user.superuser = True
        else:
            user.superuser = False
        Session.commit()
        c.user = user
        c.available_courses = filter(lambda x: x not in c.user.courses, Course.query.all())
        return render("/derived/users/manage_user.html")
    
    @require_superuser()
    def remove_course(self, id=None):
        if id is None:
            abort(404)
        user = h.get_object_or_404(User, id=id)
        course_id = request.params['course_id']
        course = h.get_object_or_404(Course, id=course_id)
        user.courses.remove(course)
        Session.commit()
        # Issue an HTTP redirect
        response.status_int = 302
        response.headers['location'] = h.url_for(controller='users', action='manage_user', id=user.id)
        return "Moved temporarily"
    
    @require_superuser()
    def add_course(self, id=None):
        if id is None:
            abort(404)
        user = h.get_object_or_404(User, id=id)
        course_id = request.params['course_id']
        course = h.get_object_or_404(Course, id=course_id)
        user.courses.append(course)
        Session.commit()
        # Issue an HTTP redirect
        response.status_int = 302
        response.headers['location'] = h.url_for(controller='users', action='manage_user', id=user.id)
        return "Moved temporarily"
    
    @require_superuser()
    def enable(self, id=None):
        if id is None:
            abort(404)
        user = h.get_object_or_404(User, id=id)
        user.enabled = True
        Session.commit()
        h.send_user_enabled_email(user)
        redirect_to(controller='users', action='manage_user', id=user.id)
    
    
    def request_enable(self, id=None):
        if id is None:
            abort(404)
        user = h.get_object_or_404(User, id=id)
        admins = User.query.filter_by(superuser=True).all()
        app_name = config['application_name']
        from_addr = config['error_email_from']
        suffix = config['email_suffix']
        subject = "New user request for "+app_name
        requested_courses = request.params["requested_course_name"]
        user.requested_courses = requested_courses
        if not request.environ.has_key('REMOTE_ADDR'):
            request.environ['REMOTE_ADDR'] = "127.0.0.1" #must be debugging locally on paste
        ip = request.environ['REMOTE_ADDR']
        for admin in admins:
            to_addr = admin.name + "@" + suffix
            body = "Dear "+admin.name+",\n\nA new user has requested an account on "+app_name+".\n\nDetails:\n\n"
            body += "username: "+user.name+"\n"
            body += "requested course(s): "+requested_courses+"\n"
            body += "timestamp: "+str(datetime.datetime.today())+"\n"
            body += "remote ip: "+ip+"\n\n\n"
            body += "Please login to https://comoto.cs.illinois.edu to approve or deny this request\n\n"
            body += "Thanks\n\n"
            body += "The "+app_name+" Team\n\n\n\n"
            body += "Please do not reply to this message, as this account is not monitored"
            message = Message(from_addr, to_addr, subject)
            message.plain = body
            message.send()
        session['flash'] = "Request Acknowledged"
        session.save()
        Session.commit()
        redirect_to(controller="login", action="index", id=None)
        
    def session_test(self):
        key = "session_test"
        if not session.has_key(key):
            session[key] = 0
        else:
            session[key] = session[key]+1
        return str(session[key])