'''
Created on Mar 31, 2010

@author: chuck
'''
#from decorator import decorator
from pylons import request
import pylons
import logging
from mossweb.lib import helpers as h
from pylons.controllers.util import abort
from mossweb.model.model import *

log = logging.getLogger(__name__)

def check_course_access(course_id):
    user = h.get_user(request.environ)
    if user.superuser:
        return
    #course = Course.get_by(id=course_id)
    course = h.get_object_or_404(Course, id=course_id)
    if course not in user.courses:
        abort(403)

def check_offering_access(offering):
    user = h.get_user(request.environ)
    if user.superuser:
        return
    if offering.course not in user.courses:
        abort(403)
        
def check_fileset_access(fileset_list):
    user = h.get_user(request.environ)
    if user.superuser:
        return
    for fileset in fileset_list:
        if fileset.course not in user.courses:
            abort(403)
            
def check_assignment_access(assignment):
    user = h.get_user(request.environ)
    if user.superuser:
        return
    if assignment.course not in user.courses:
        abort(403)
        
def check_file_access(submission_file):
    user = h.get_user(request.environ)
    if user.superuser:
        return
    if submission_file.submission.fileset.course not in user.courses:
        abort(403)
        
def check_student_access(student):
    user = h.get_user(request.environ)
    if user.superuser:
        return
    allow = False
#    for sub in student.submissions:
#        if sub.offering.course in user.courses:
#            allow = True
    for offering in student.offerings:
        if offering.course in user.courses:
            allow = True
    if not allow:
        abort(403)
        
def check_image_access(image):
    try:
        owner_type = image.owner_type
        owner_id = image.owner_id
        eval_str = owner_type+".get_by(id="+str(owner_id)+")"
        obj = eval(eval_str)
        if obj is None:
            abort(404)
        if owner_type == "MossAnalysis":
            check_assignment_access(obj.analysis.assignment)
        else:
            log.warn("No programmed handler for check_image_access with Image owner type: "+owner_type)
            abort(403)
    except:
        abort(403)
    