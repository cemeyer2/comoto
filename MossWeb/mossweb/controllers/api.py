import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to, redirect

from mossweb.lib.base import BaseController, render

from mossweb.lib import helpers as h
from mossweb.model.model import *
from mossweb.model import Session

import xmlrpclib
from pylons.controllers import XMLRPCController

log = logging.getLogger(__name__)

from mossweb.lib.api_helpers import *
import traceback, sys
from mossweb.lib.decorators import require_enabled_user

class ApiController(XMLRPCController):
    
    #http://www.mail-archive.com/pylons-discuss@googlegroups.com/msg06857.html
    def __call__(self, environ, start_response):
        # Wrap an exception in an XMLRPC fault
        try:
            retval = XMLRPCController.__call__(self, environ, start_response)
            Session.remove()
            return retval
        except:
            log.debug(traceback.format_exc())
            Session.remove()
            return xmlrpclib.Fault(0, "Application Error")
    
    
    XMLRPCController.allow_none = True
    
    def getCourses(self, extra_offering_info=False):
        """Returns an array of courses for the currently authenticated user. Each element
        of the array is a struct containing data about each course. If the currently authenticated
        user is not associated with any courses, an empty array is returned. 
        If the optional parameter extra_offering_info is set to True, then LDAP information from the
        UIUC AD and a list of student ids in the offering will be returned for each offering if that offering
        was linked to sections in the directory using the web interface.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        retval = []
        user = h.get_user(request.environ)
        for course in user.courses:
            retval.append(xmlrpcify_course(course, extra_offering_info))
        return retval
    getCourses.signature = [['array'], ['array', 'boolean']]
    
    def getAssignments(self, course_id):
        """Returns an array of assignments for the requested course. If the requested course
        has no assignments, an empty array is returned. An XML-RPC fault is sent with the 
        corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier parameter")
        retval = []
        course = get_object_or_none(Course, id=course_id)
        if course is None:
            return xmlrpclib.Fault(0, "No such course exists")
        if not api_check_course_access(course_id):
            return xmlrpclib.Fault(0, "Course security check failed")
        assignments = course.assignments
        for assignment in assignments:
            retval.append(xmlrpcify_assignment(assignment))
        return retval
    getAssignments.signature = [['array','int']] #return type, param types
    
    def getAnalysis(self, analysis_id):
        """Returns a struct representing the analysis requested by its id.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        analysis = get_object_or_none(Analysis, id=analysis_id)
        if analysis is None:
            return xmlrpclib.Fault(0, "No such analysis exists")
        if not api_check_assignment_access(analysis.assignment):
            return xmlrpclib.Fault(0, "Assignment security check failed")
        return xmlrpcify_analysis(analysis)
    getAnalysis.signature = [['struct','int']]
    
    def getSubmission(self, submission_id, full_student_data=False):
        """Returns a struct representing the submission requested by its id. If the optional parameter full_student_data is set
        to True, then all student data will be returned for this submission if the submission being fetched is a student submission,
        otherwise this parameter has no effect.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        submission = get_object_or_none(Submission, id=submission_id)
        if submission is None:
            return xmlrpclib.Fault(0, "No such submission exists")
        if not api_check_fileset_access([submission.fileset]):
            return xmlrpclib.Fault(0, "File set security check failed for requested submission")
        return xmlrpcify_submission(submission, full_student_data)    
    getSubmission.signature = [['struct', 'int'], ['struct', 'int', 'boolean']]
    
    def getReport(self, id):
        """Returns a struct representing the report requested by its id.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        report = get_object_or_none(Report, id=id)
        if report is None:
            return xmlrpclib.Fault(0, "No such report exists")
        if not api_check_assignment_access(report.assignment):
            return xmlrpclib.Fault(0, "Assignment security check failed for requested report")
        retval = xmlrpcify_report(report)
        return retval
    getReport.signature = [['struct', 'int']]
    
    def getMossAnalysis(self, id, categorize_matches=False, minimum_match_score=0, single_student_max_matches_lower_bound=-1, single_student_max_matches_upper_bound=-1):
        """Returns a struct representing the moss analysis requested by its id. If the optional parameter categorize_matches is set to True, then
        three additional lists will be returned as part of the struct: moss matches with the solution, moss matches within the same semester, and moss matches across semesters.
        The default for categorize_matches is False. If the optional parameter minimum_match_score is supplied, then all lists of moss matches will be filtered before being returned such that only matches
        with at least one score component greater than or equal to minimum_match_score are included. The default for minimum_match_score is 0. If the optional parameter single_student_max_matches_lower_bound is supplied,
        then all returned lists of moss matches will be filtered such that only matches with at least one student appearing in less than or equal to single_student_max_matches_lower_bound 
        will be included. If the optional parameter single_student_max_matches_upper_bound is supplied, then all lists of retuned moss matches will be filtered such that matches are included
        if and only if either student in the match appears in less than single_student_max_matches_lower_bound and neither student in the match appears in more than single_student_max_matches_upper_bound.
        The default for single_student_max_matches_lower_bound and single_student_max_matches_upper_bound is -1, which indicates no lower bound and unlimited upper bound.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        analysis = get_object_or_none(MossAnalysis, id=id)
        if analysis is None:
            return xmlrpclib.Fault(0, "No such moss analysis exists")
        if not api_check_assignment_access(analysis.analysis.assignment):
            return xmlrpclib.Fault(0, "Assignment security check failed for requested moss analysis")
        return xmlrpcify_moss_analysis(analysis, categorize_matches, minimum_match_score, single_student_max_matches_lower_bound, single_student_max_matches_upper_bound)
    getMossAnalysis.signature = [['struct','int'], ['struct', 'int', 'boolean'], ['struct','int', 'boolean', 'int'], ['struct', 'int','boolean', 'int', 'int'], ['struct', 'int','boolean', 'int', 'int', 'int']]
    
    def getStudent(self, id, show_history=False, history_minimum_match_score=0):
        """Returns a struct representing the student requested by its id.
        If the optional parameter show_history is set to True, then the returned struct will include a list of moss matches
        in which the requested student appears. The default for show_history is False. If the optional parameter
        history_minimum_match_score is supplied, then the list of returned moss matches will be filtered such that only matches
        with at least one score component greater than or equal to history_minimum_match_score are included. This parameter
        only has meaning if show_history is set to True. The default for history_minimum_match_score is 0.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        student = get_object_or_none(Student, id=id)
        if student is None:
            return xmlrpclib.Fault(0, "No such student exists")
        if not api_check_student_access(student):
            return xmlrpclib.Fault(0, "Student security check failed")
        user = h.get_user(request.environ)
        #pretty much a copy paste job from history controller
        #TODO: refactor this into a common helper function
        submissions = filter(lambda submission: submission.offering.course in user.courses, student.submissions)
        matches = []
        if show_history:
            ids = [s.id for s in submissions]
            matches.extend(MossMatch.query.join(MossMatch.submission1).filter(Submission.id.in_(ids)).all())
            matches.extend(MossMatch.query.join(MossMatch.submission2).filter(Submission.id.in_(ids)).all())
            matches = filter(lambda match: match.mossAnalysis.analysis.assignment.course in user.courses, matches)
        return xmlrpcify_student(student, submissions, matches, show_history, history_minimum_match_score, False)
    getStudent.signature = [['struct', 'int'], ['struct','int','boolean'], ['struct', 'int', 'boolean', 'int']]
    
    def getStudents(self, ids, show_history=False, history_minimum_match_score=0):
        """Returns an array of structs representing the students requested by their ids.
        If the optional parameter show_history is set to True, then the returned array of structs will include a list of moss matches
        in which the requested student appears for each student struct. The default for show_history is False. If the optional parameter
        history_minimum_match_score is supplied, then the list of returned moss matches for each student struct will be filtered 
        such that only matches with at least one score component greater than or equal to history_minimum_match_score are included. 
        This parameter only has meaning if show_history is set to True. The default for history_minimum_match_score is 0.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if ids is None:
            return xmlrpclib.Fault(0, "Invalid array of identifiers")
        retval = []
        for id in ids:
            if type(id) != int:
                return xmlrpclib.Fault(0, "Invalid identifier")
            retval.append(self.getStudent(id, show_history, history_minimum_match_score)) #what happens if we append a fault?
        return retval
    getStudents.signature = [['array','array'],['array','array', 'boolean'], ['array','array', 'boolean', 'int']]
    
    def getStudentByNetid(self, netid, show_history=False, history_minimum_match_score=0):
        """Returns a struct representing the student requested by its netid.
         If the optional parameter show_history is set to True, then the returned struct will include a list of moss matches
        in which the requested student appears. The default for show_history is False. If the optional parameter
        history_minimum_match_score is supplied, then the list of returned moss matches will be filtered such that only matches
        with at least one score component greater than or equal to history_minimum_match_score are included. This parameter
        only has meaning if show_history is set to True. The default for history_minimum_match_score is 0.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if netid is None:
            return xmlrpclib.Fault(0,"Invalid netid")
        student = get_object_or_none(Student, netid=netid)
        if student is None:
            return xmlrpclib.Fault(0,"No such student exists")
        return self.getStudent(student.id, show_history, history_minimum_match_score)
    getStudentByNetid.signature = [['struct', 'string'], ['struct','string','boolean'], ['struct','string','boolean', 'int']]
    
    def getSubmissionFile(self, id, highlighted=False):
        """Returns a struct representing the submission file requested by its id. If the optional boolean parameter
        is set to True, then html format syntax highlighted code will also be produced.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        file = get_object_or_none(SubmissionFile, id=id)
        if file is None:
            return xmlrpclib.Fault(0, "No such submission file exists")
        if not api_check_fileset_access([file.submission.fileset]):
            return xmlrpclib.Fault(0, "File set security check failed for requested submission file")
        return xmlrpcify_submission_file(file, highlighted)
    getSubmissionFile.signature = [['struct', 'int'], ['struct', 'int', 'boolean']]
    
    def getFileSet(self, id, full_submission_info=False, extra_offering_info=False):
        """Returns a struct representing the FileSet requested by its id.
        If the optional parameter extra_offering_info is set to True, then LDAP information from the
        UIUC AD and a list of student ids in the offering will be returned for each offering if that offering
        was linked to sections in the directory using the web interface.
        If the optional parameter full_submission_info is set to True, then all submissions for this file set
        will be returned in addition to their identifiers.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        fileset = get_object_or_none(FileSet, id=id)
        if fileset is None:
            return xmlrpclib.Fault(0, "No such file set exists")
        if not api_check_fileset_access([fileset]):
            return xmlrpclib.Fault(0, "File set security check failed")
        return xmlrpcify_fileset(fileset, full_submission_info, extra_offering_info)
    getFileSet.signature = [['struct', 'int'], ['struct','int','boolean'], ['struct','int','boolean','boolean']]
    
    def getFileSets(self, ids, full_submission_info=False, extra_offering_info=False):
        """Returns an array of structs representing the FileSets requested by their ids.
        If the optional parameter extra_offering_info is set to True, then LDAP information from the
        UIUC AD and a list of student ids in the offering will be returned for each offering if that offering
        was linked to sections in the directory using the web interface.
        If the optional parameter full_submission_info is set to True, then all submissions for each file set
        will be returned in addition to their identifiers.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if ids is None:
            return xmlrpclib.Fault(0,"Invalid identiifers")
        for id in ids:
            if type(id) is not int:
                return xmlrpclib.Fault(0, "Invalid identifier")
        retval = []
        for id in ids:
            retval.append(self.getFileSet(id, full_submission_info, extra_offering_info))
        return retval
    getFileSets.signature = [['array', 'array'], ['array','array','boolean'], ['array','array','boolean','boolean']]
    
    def getAnalysisPseudonym(self, id, full_submission_data=False):
        """Returns a struct representing the AnalysisPseudonym requested by its id.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        log.debug("starting for id="+str(id))
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        log.debug("getting object")
        ap = get_object_or_none(AnalysisPseudonym, id=id)
        log.debug(str(ap))
        if ap is None:
            return xmlrpclib.Fault(0, "No such analysispseudonym exists")
        log.debug(str(ap.analysis))
        if not api_check_assignment_access(ap.analysis.assignment):
            return xmlrpclib.Fault(0, "Analysis security check failed")
        log.debug("xmlrpcifying")
        return xmlrpcify_analysis_pseudonym(ap, full_submission_data)
        #return {}
    getAnalysisPseudonym.signature = [['struct', 'int'], ['struct', 'int', 'boolean']]

    def getAssignment(self, id):
        """Returns a struct representing the Assignment requested by its id.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        assignment = get_object_or_none(Assignment, id=id)
        if assignment is None:
            return xmlrpclib.Fault(0, "No such assignment exists")
        if not api_check_assignment_access(assignment):
            return xmlrpclib.Fault(0, "Assignment security check failed")
        return xmlrpcify_assignment(assignment)
    getAssignment.signature = [['struct', 'int']]

    def getCourse(self, id, extra_offering_info=False):
        """Returns a struct representing the Course requested by its id.
                If the optional parameter extra_offering_info is set to True, then LDAP information from the
        UIUC AD and a list of student ids in the offering will be returned for each offering if that offering
        was linked to sections in the directory using the web interface.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        course = get_object_or_none(Course, id=id)
        if course is None:
            return xmlrpclib.Fault(0, "No such course exists")
        if not api_check_course_access(course.id):
            return xmlrpclib.Fault(0, "File set security check failed")
        return xmlrpcify_course(course, extra_offering_info)
    getCourse.signature = [['struct', 'int'], ['struct', 'int', 'boolean']]

    def getJplagAnalysis(self, id):
        """Not implemented
        """
        return {}
    getJplagAnalysis.signature = [['struct','int']]

    def getMossMatch(self, id):
        """Returns a struct representing the MossMatch requested by its id.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        match = get_object_or_none(MossMatch, id=id)
        if match is None:
            return xmlrpclib.Fault(0, "No such moss match exists")
        if not api_check_assignment_access(match.mossAnalysis.analysis.assignment):
            return xmlrpclib.Fault(0, "Assignment security check failed")
        return xmlrpcify_moss_match(match)
    getMossMatch.signature = [['struct', 'int']]

    def getMossReport(self, id):
        """Returns a struct representing the MossReport requested by its id.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        report = get_object_or_none(MossReport, id=id)
        if report is None:
            return xmlrpclib.Fault(0, "No such moss report exists")
        if not api_check_assignment_access(report.report.assignment):
            return xmlrpclib.Fault(0, "Assignment security check failed")
        return xmlrpcify_mosss_report(report)
    getMossReport.signature = [['struct', 'int']]

    def getOffering(self, id, extra_info=False):
        """Returns a struct representing the Offering requested by its id.
             If the optional parameter extra_info is set to True, then LDAP information from the
        UIUC AD and a list of student ids in the offering will be returned for each offering if that offering
        was linked to sections in the directory using the web interface.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        offering = get_object_or_none(Offering, id=id)
        if offering is None:
            return xmlrpclib.Fault(0, "No such offering exists")
        if not api_check_course_access(offering.course.id):
            return xmlrpclib.Fault(0, "Course security check failed")
        return xmlrpcify_offering(offering, extra_info)
    getOffering.signature = [['struct', 'int'], ['struct','int','boolean']]

    def getSemester(self, id):
        """Returns a struct representing the Semester requested by its id.
        An XML-RPC fault is sent with the corresponding error message if there is an error condition or a security check failure.
        """
        if id is None:
            return xmlrpclib.Fault(0, "Invalid identifier")
        semester = get_object_or_none(Semester, id=id)
        if semester is None:
            return xmlrpclib.Fault(0, "No such semester exists")
        #no security checks for semester, since they dont link to anything
        return xmlrpcify_semester(semester)
    getSemester.signature = [['struct', 'int']]
    