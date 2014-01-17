'''
Created on Oct 8, 2010

This file is a collection of helper functions to convert
comoto model objects to xmlrpc valid types

@author: Charlie Meyer <cemeyer2@illinois.edu>
'''
import logging
log = logging.getLogger(__name__)
from mossweb.model.model import *
from pygments.lexers import guess_lexer_for_filename
from pygments import highlight
from pygments.formatters import HtmlFormatter
import xmlrpclib, sys
from pylons import request
from mossweb.lib import helpers as h
from mossweb.lib import ldap_helpers as lh

def __model_list_to_id_list(model_list):
    retval = []
    if model_list is None or not isinstance(model_list, list):
        return retval
    for model in model_list:
        if model is not None:
            retval.append(__safe_property(model,"","id"))
    return retval

def __safe_property(obj, default, *args):
    property = obj
    if property is None:
            return default
    for prop in args:
        try:
            property = property.__getattribute__(prop)
            if property is None:
                return default
        except:
            return default
    return property

def get_object_or_none(model, **kw):
    obj = model.get_by(**kw)
    return obj

def xmlrpcify_course(course, extra_offering_info=False):
    if not isinstance(course, Course) or course is None:
        return {}
    retval = {}
    retval["class"] = "Course"
    retval["name"] = __safe_property(course, "", "name")
    retval["id"] = __safe_property(course, -1, "id")
    retval["assignment_ids"] = __model_list_to_id_list(course.assignments)
    retval["user_ids"] = __model_list_to_id_list(course.users)
    retval["fileset_ids"] = __model_list_to_id_list(course.filesets)
    retval['ldap_dn'] = __safe_property(course, "", "dn")
    offerings = []
    for offering in course.offerings:
        offerings.append(xmlrpcify_offering(offering, extra_offering_info))
    retval["offerings"] = offerings
    return retval

def xmlrpcify_offering(offering, extra_info=False):
    if not isinstance(offering, Offering) or offering is None:
        return {}
    retval = {}
    retval["class"] = "Offering"
    retval["id"] = __safe_property(offering, -1, "id")
    retval["course_id"] = __safe_property(offering, -1, "course", "id")
    retval["fileset_ids"] = __model_list_to_id_list(offering.filesets)
    retval["semester"] = xmlrpcify_semester(offering.semester)
    retval['ldap_dns'] = __safe_property(offering, [], "dns")
    if extra_info:
        offering_info = lh.get_offering_info(offering.dns)
        offering_info = map(lambda tup: tup[1],offering_info)
        retval['offering_info'] = __encode_list(offering_info)
        student_dns = lh.get_student_dns_for_offering(offering)
        roster = lh.get_students_for_dns(student_dns)
        retval['roster_student_ids'] = __model_list_to_id_list(roster)
    return retval

def xmlrpcify_semester(semester):
    if not isinstance(semester, Semester) or semester is None:
        return {}
    retval = {}
    retval["class"] = "Semester"
    retval["id"] = __safe_property(semester, -1, "id")
    retval["season"] = __safe_property(semester, "", "season")
    retval["year"] = __safe_property(semester,-1, "year")
    #retval["is_solution"] = __safe_property(semester.isSolution, False) #we don't need this anymore since we have type
    retval["type"] = __safe_property(semester, "semester", "row_type") #this is the inheritance type, either semester, solutionsemester, or basesemester
    return retval

def xmlrpcify_assignment(assignment):
    if not isinstance(assignment, Assignment) or assignment is None:
        return {}
    assignment_dict = {}
    assignment_dict["name"] = __safe_property(assignment, "", "name")
    assignment_dict["language"] = __safe_property(assignment, "", "language")
    assignment_dict["analysis_id"] = __safe_property(assignment, -1, "analysis", "id")
    assignment_dict["report_id"] = __safe_property(assignment, -1, "report", "id")
    assignment_dict["id"] = __safe_property(assignment, -1, "id")
    assignment_dict["fileset_ids"] = __model_list_to_id_list(assignment.filesets)
    assignment_dict["course_id"] = __safe_property(assignment, -1, "course", "id")
    moss_analysis_pruned_offering = __safe_property(assignment, {}, "analysis", "mossAnalysis", "prunedOffering")
    assignment_dict['moss_analysis_pruned_offering'] = {}
    if moss_analysis_pruned_offering is not {}:
        assignment_dict['moss_analysis_pruned_offering'] = xmlrpcify_offering(moss_analysis_pruned_offering) 
    return assignment_dict

def xmlrpcify_analysis(analysis):
    if not isinstance(analysis, Analysis) or analysis is None:
        return {}
    retval = {}
    retval["class"] = "Analysis"
    retval["assignment_id"] = __safe_property(analysis, -1, "assignment", "id")
    retval["id"] = __safe_property(analysis, -1, "id")
    ts = __safe_property(analysis, 0, "timestamp")
    tup = 0
    if ts != 0:
        tup = ts.timetuple()        
    retval["timestamp"] = xmlrpclib.DateTime(tup)
        
    retval["moss_analysis_id"] = __safe_property(analysis, -1, "mossAnalysis", "id")
    retval["jplag_analysis_id"] = __safe_property(analysis, -1, "jPlagAnalysis", "id")
        
    #retval["work_directory"] = __safe_property(analysis, "", "workDirectory") not needed
    #retval["web_directory"] = __safe_property(analysis, "", "webDirectory") not needed
    retval["complete"] = __safe_property(analysis, False, "complete")
    pseudos = []
    for pseudo in analysis.analysisPseudonyms:
        pseudos.append(xmlrpcify_analysis_pseudonym(pseudo))
    retval["analysis_pseudonyms"] = pseudos
    return retval

def xmlrpcify_moss_analysis(analysis, categorize_matches=False, minimum_match_score=0, single_student_max_matches_lower_bound=-1, single_student_max_matches_upper_bound=-1):
    if not isinstance(analysis, MossAnalysis) or analysis is None:
        return {}
    retval = {}
    retval["class"] = "MossAnalysis"
    retval["id"] = __safe_property(analysis, -1, "id")
    retval["analysis_id"] = __safe_property(analysis, -1, "analysis", "id")
    retval['pruned'] = __safe_property(analysis, "False", "pruned")
    retval['pruned_offering_id'] = __safe_property(analysis, -1, "prunedOffering", "id")
    matches = analysis.matches
    matches = filter(lambda m: not m.hidden, matches)
    from mossweb.lib.helpers import filter_moss_matches_to_minimum_score
    matches = filter_moss_matches_to_minimum_score(matches, minimum_match_score)
    matches.sort()
    matches.reverse()
    if single_student_max_matches_lower_bound > 0:
        netid_dict = {}
        for match in matches:
            def add_netid(submission):
                if isinstance(submission, StudentSubmission):
                    netid_dict[submission.student.netid] = 0
            add_netid(match.submission1)
            add_netid(match.submission2)
        def filter_fun(match):
            if isinstance(match.submission1, StudentSubmission) and isinstance(match.submission2, StudentSubmission):
                netid1 = match.submission1.student.netid
                netid2 = match.submission2.student.netid
                netid_dict[netid1] = netid_dict[netid1] + 1
                netid_dict[netid2] = netid_dict[netid2] + 1
                if netid_dict[netid1] <= single_student_max_matches_lower_bound or netid_dict[netid2] <= single_student_max_matches_lower_bound:
                    if single_student_max_matches_upper_bound > 0 and (netid_dict[netid1] > single_student_max_matches_upper_bound or netid_dict[netid2] > single_student_max_matches_upper_bound):
                        return False
                    return True
                else:
                    return False
            return True
        matches = filter(filter_fun, matches)
    all_matches = []
    for match in matches:
        all_matches.append(xmlrpcify_moss_match(match))
    retval["matches"] = all_matches
    if single_student_max_matches_upper_bound < single_student_max_matches_lower_bound:
         single_student_max_matches_upper_bound = single_student_max_matches_lower_bound
    if categorize_matches:
        solutionMatches = filter(lambda x: isinstance(x.submission1, SolutionSubmission) or isinstance(x.submission2, SolutionSubmission), matches)
        crossSemesterMatches = filter(lambda x: isinstance(x.submission1, StudentSubmission) and isinstance(x.submission2, StudentSubmission) and x.submission1.offering.id != x.submission2.offering.id, matches)
        sameSemesterMatches = filter(lambda x: isinstance(x.submission1, StudentSubmission) and isinstance(x.submission2, StudentSubmission) and x.submission1.offering.id == x.submission2.offering.id, matches)
        retval['solution_matches'] = map(xmlrpcify_moss_match, solutionMatches)
        retval['cross_semester_matches'] = map(xmlrpcify_moss_match, crossSemesterMatches)
        retval['same_semester_matches'] = map(xmlrpcify_moss_match, sameSemesterMatches)
    return retval

def xmlrpcify_moss_match(match):
    if not isinstance(match, MossMatch) or match is None:
        return {}
    retval = {}
    retval["class"] = "MossMatch"
    retval["id"] = __safe_property(match, -1, "id")
    retval["moss_analysis_id"] = __safe_property(match, -1, "mossAnalysis", "id")
    retval["submission_1_id"] = __safe_property(match, -1, "submission1", "id")
    retval["submission_2_id"] = __safe_property(match, -1, "submission2", "id")
    retval["score1"] = __safe_property(match, -1, "score1")
    retval["score2"] = __safe_property(match, -1, "score2")
    retval["hidden"] = __safe_property(match, False, "hidden")
    url = __api_view_moss_result_url(match)
    proto = request.environ['wsgi.url_scheme'] #http or https
    host = request.environ['HTTP_HOST'] #localhost:5000
    retval["link"] = proto + "://" + host + url
    #from pprint import pformat
    #log.debug(pformat(retval))
    return retval

def xmlrpcify_analysis_pseudonym(pseudo, full_submission_data=False):
    if not isinstance(pseudo, AnalysisPseudonym) or pseudo is None:
        return {}
    retval = {}
    retval["class"] = "AnalysisPseudonym"
    retval["id"] = __safe_property(pseudo, -1, "id")
    retval["analysis_id"] = __safe_property(pseudo, -1, "analysis", "id")
    retval["submission_id"] = __safe_property(pseudo, -1, "submission", "id") #change this to include submission struct, maybe?
    retval["pseudonym"] = __safe_property(pseudo, "", "pseudonym")
    if full_submission_data:
        retval['submission'] = xmlrpcify_submission(pseudo.submission, True)
    #from pprint import pformat
    #log.debug(pformat(retval))
    return retval

def xmlrpcify_submission(submission, full_student_data=False):
    if not isinstance(submission, Submission) or submission is None:
        return {}
    retval = {}
    retval["class"] = "Submission"
    retval["id"] = __safe_property(submission, -1, "id")
    retval["submission_file_ids"] = __model_list_to_id_list(submission.submissionFiles)
    retval["fileset_id"] = __safe_property(submission, -1, "fileset", "id")
    retval["analysis_pseudonym_ids"] = __model_list_to_id_list(submission.analysisPseudonyms)
        
    if isinstance(submission, StudentSubmission):
        retval["offering_id"] = __safe_property(submission, -1, "offering", "id")
        retval["student_id"] = __safe_property(submission, -1, "student", "id")
        retval["partner_ids"] = __model_list_to_id_list(__safe_property(submission, [], "partners"))
        if full_student_data:
            user = h.get_user(request.environ)
            submissions = filter(lambda submission: submission.offering.course in user.courses, submission.student.submissions)
            retval['student'] = xmlrpcify_student(submission.student, submissions, [], False, 0, False)
        
    retval["type"] = __safe_property(submission, "submission", "row_type")
    return retval

def xmlrpcify_report(report):
    if not isinstance(report, Report) or report is None:
        return {}
    retval = {}
    retval["class"] = "Report"
    retval["id"] = __safe_property(report, -1, "id")
    retval["assignment_id"] = __safe_property(report, -1, "assignment", "id")
    retval["complete"] = __safe_property(report, False, "complete")
    retval["moss_report"] = xmlrpcify_mosss_report(report.mossReport)
    retval["jplag_report"] = xmlrpcify_jplag_report(report.jPlagReport)

    return retval;

def xmlrpcify_mosss_report(report):
    if not isinstance(report, MossReport) or report is None:
        return {}
    retval = {}
    retval["class"] = "MossReport"
    retval["id"] = __safe_property(report, -1, "id")
    retval["report_id"] = __safe_property(report, -1, "report", "id")
    retval["moss_report_file_ids"] = __model_list_to_id_list(report.mossReportFiles)
    
    return retval;

def xmlrpcify_jplag_report(report):
    if not isinstance(report, MossReport) or report is None:
        return {}
    retval = {}
    retval["class"] = "JPlagReport"
    retval["id"] = __safe_property(report, -1, "id")
    retval["report_id"] = __safe_property(report, -1, "report", "id")
    return retval;

def xmlrpcify_student(student, submissions, matches=[], show_history=False, history_minimum_match_score=0, ldap_populate=True):
    if not isinstance(student, Student) or student is None:
        return {}
    for sub in submissions:
        if not isinstance(sub, Submission):
            return {}
    for match in matches:
        if not isinstance(match, MossMatch):
            return {}
    if ldap_populate:
        lh.populate_student_from_active_directory(student)
    retval = {}
    retval["class"] = "Student"
    retval["id"] = __safe_property(student, -1, "id")
    retval["netid"] = __safe_property(student, "", "netid")
    retval["level_name"] = __safe_property(student,"","levelName")
    retval["program_name"] = __safe_property(student,"","programName")
    retval["given_name"] = __safe_property(student,"","givenName")
    retval["display_name"] = __safe_property(student,"","displayName")
    retval["sur_name"] = __safe_property(student,"","surName")
    retval["left_uiuc"] = __safe_property(student,"","leftUIUC")
    retval["submission_ids"] = __model_list_to_id_list(submissions)
    retval["directory_info"] = lh.get_student_directory_info(student)
    if show_history:
        from mossweb.lib.helpers import filter_moss_matches_to_minimum_score
        retval["matches"] = map(xmlrpcify_moss_match, filter_moss_matches_to_minimum_score(matches, history_minimum_match_score))
    proto = request.environ['wsgi.url_scheme'] #http or https
    host = request.environ['HTTP_HOST'] #localhost:5000
    retval["history_link"] = proto + "://" + host + h.url_for(controller="history", action="view", id=student.netid)
    retval['ldap_dn'] = __safe_property(student, "", "dn")
    return retval

def xmlrpcify_submission_file(file, highlighted):
    if not isinstance(file, SubmissionFile) or file is None:
        return {}
    retval = {}
    retval["class"] = "SubmissionFile"
    retval["id"] = __safe_property(file, -1, "id")
    retval["submission_id"] = __safe_property(file, -1, "submission", "id")
    retval["name"] = __safe_property(file, "", "name")
    retval["content"] = __safe_property(file, "", "content")
    retval["meta"] = __safe_property(file, False, "meta")
    if highlighted == True:
        lexer = guess_lexer_for_filename(__safe_property(file, "", "name"), __safe_property(file, "", "content"))        
        formatter = HtmlFormatter(full=True, linenos='table', nobackground=True)
        retval["highlighted"] = highlight(__safe_property(file, "", "content"), lexer, formatter)
    return retval

def xmlrpcify_fileset(fileset, full_submission_info=False, extra_offering_info=False):
    if not isinstance(fileset, FileSet) or fileset is None:
        return {}
    retval = {}
    retval["class"] = "FileSet"
    retval["id"] = __safe_property(fileset, -1, "id")
    retval["name"] = __safe_property(fileset, "", "name");
    retval["submission_ids"] = __model_list_to_id_list(fileset.submissions)
    retval["assignment_ids"] = __model_list_to_id_list(fileset.assignments)
    retval["offering"] = xmlrpcify_offering(fileset.offering, extra_offering_info)
    retval["course_id"] = __safe_property(fileset, -1, "course", "id")
    #retval["is_solution_set"] = fileset.isSolutionSet #dont need anymore since we have type attribute
    #retval["tempdir"] = fileset.tempDir #not needed
    ts = __safe_property(fileset, 0, "timestamp")
    tup = 0
    if ts != 0:
        tup = ts.timetuple()
    retval["timestamp"] = xmlrpclib.DateTime(tup)
    retval["is_complete"] = __safe_property(fileset, False, "isComplete")
    retval["type"] = __safe_property(fileset, "fileset", "row_type")
    if full_submission_info:
        subs = []
        for sub in fileset.submissions:
            subs.append(xmlrpcify_submission(sub, True))
        retval['submissions'] = subs
    
    return retval

def xmlrpcify_user(user):
    if not isinstance(user, User) or user is None:
        return {}
    retval = {}
    retval["class"] = "User"
    retval['name'] = __safe_property(user, "", "name")
    retval['superuser'] = __safe_property(user, False, "superuser")
    retval['courses'] = __model_list_to_id_list(user.courses)
    retval['enabled'] = __safe_property(user, True, "enabled")
    retval['given_name'] = __safe_property(user, "", "givenName")
    retval['sur_name'] = __safe_property(user, "", "surName")
    retval['ldap_dn'] = __safe_property(user, "", "dn")

def __api_view_moss_result_url(mossmatch):
    if not isinstance(mossmatch, MossMatch) or mossmatch is None:
        return ""
    report = __safe_property(mossmatch, None, "mossAnalysis", "analysis", "assignment", "report", "mossReport")
    if report is None:
        return ""
    file = get_object_or_none(MossReportFile, name=__safe_property(mossmatch, "", "link"), mossReport=report)
    if file is None:
        return ""
    id = __safe_property(file, -1, "id")
    if id is None:
        return ""
    return h.url_for(controller="view_analysis", action="view_moss_result", id=id)

#ACCESS CHECKS TAILORED FOR API:
def api_check_course_access(course_id):
    user = h.get_user(request.environ)
    if user.superuser:
        return True
    course = get_object_or_none(Course, id=course_id)
    if course is None:
        return False
    if course not in user.courses:
        return False
    return True

def api_check_fileset_access(fileset_list):
    user = h.get_user(request.environ)
    if user.superuser:
        return True
#    if user.superuser:
#        return
    for fileset in fileset_list:
        if fileset.course not in user.courses:
            return False
    return True
            
def api_check_assignment_access(assignment):
    user = h.get_user(request.environ)
    if user.superuser:
        return True    
#    if user.superuser:
#        return
    if assignment.course not in user.courses:
        return False
    return True

def api_check_student_access(student):
    user = h.get_user(request.environ)
    if user.superuser:
        return True
    allow = False
    for sub in student.submissions:
        if sub.offering.course in user.courses:
            allow = True
    return allow

def __encode(item):
    if type(item) == str:
        try:
            return item.encode('UTF-8', 'xmlcharrefreplace')
        except:
            return ""
    elif type(item) == long:
        return int(item)
    else:
        return item

def __encode_list(l):
    retval = []
    for item in l:
        if type(item) == list:
            retval.append(__encode_list(item))
        elif type(item) == dict:
            retval.append(__encode_struct(item))
        else:
            retval.append(__encode(item))
    return retval

def __encode_struct(s):
    retval = {}
    for key,value in s.items():
        if type(value) == list:
            retval[__encode(key)] = __encode_list(value)
        elif type(value) == dict:
            retval[__encode(key)] = __encode_struct(value)
        else:
            retval[__encode(key)] = __encode(value)
    return retval
        
