'''
Created on Oct 12, 2010

@author: chuck
'''

from mossweb.model.model import *
from pylons.controllers.util import abort
from mossweb.lib.helpers import view_moss_result_url, url_for
from webhelpers.html import literal

def __view_history_link(submission):
    if not isinstance(submission, Submission):
        abort(404)
    if isinstance(submission, StudentSubmission):
        return literal("<a href='"+url_for(controller="history", action="view", id=submission.student.netid)+"'>"+submission.student.netid+"</a>")
    elif isinstance(submission, SolutionSubmission):
        return "Solution"
    else:
        return "-"

def __safe_submission_to_str(submission):
    if not isinstance(submission, Submission):
        abort(404)
    if isinstance(submission, StudentSubmission):
        return submission.student.netid
    elif isinstance(submission, SolutionSubmission):
        return "Solution"
    else:
        return "-"

def moss_match_to_history_str(match, student):
    if not isinstance(match, MossMatch) or not isinstance(student, Student):
        abort(404)
    analysis = match.mossAnalysis.analysis
    assignment = analysis.assignment
    course_assignment = assignment.course.name + " " + assignment.name
    
    offering_str_sub1 = match.submission1.fileset.offering.to_str()
    offering_str_sub2 = match.submission2.fileset.offering.to_str()
    
    match_text = ""
    if match.submission1.row_type == 'studentsubmission' and student == match.submission1.student:
        match_text = str(match.score1) + "% of " + __safe_submission_to_str(match.submission1) + " ("+offering_str_sub1+") matched " + str(match.score2) + "% of " + __view_history_link(match.submission2) +" ("+offering_str_sub2+")"
    elif match.submission2.row_type == 'studentsubmission' and student == match.submission2.student:
        match_text = str(match.score1) + "% of " + __view_history_link(match.submission1) + " ("+offering_str_sub1+") matched " + str(match.score2) + "% of " + __safe_submission_to_str(match.submission2) +" ("+offering_str_sub2+")"
    
    url = literal("<a href='"+view_moss_result_url(match)+"' target='_blank'>details</a>")
    
    retval = course_assignment + " - " + match_text + " - " + url
    return retval

def moss_match_to_history_row_str(match, student):
    if not isinstance(match, MossMatch) or not isinstance(student, Student):
        abort(404)
    analysis = match.mossAnalysis.analysis
    assignment = analysis.assignment
    offering_str_sub1 = match.submission1.fileset.offering.to_str()
    offering_str_sub2 = match.submission2.fileset.offering.to_str()
    
    def add_col(text):
        return "<td>"+str(text)+"</td>"
    
    row = "<tr>"
    row += add_col(assignment.course.name)
    row += add_col(assignment.name)
    if match.submission1.row_type == 'studentsubmission' and student == match.submission1.student:
        row += add_col(__safe_submission_to_str(match.submission1) + " - "+ offering_str_sub1+" - "+ str(match.score1)+"%")
        row += add_col(__view_history_link(match.submission2) + " - "+ offering_str_sub2+" - "+ str(match.score2)+"%")
    elif match.submission2.row_type == 'studentsubmission' and student == match.submission2.student:
        row += add_col(__safe_submission_to_str(match.submission2) + " - "+ offering_str_sub2+" - "+ str(match.score2)+"%")
        row += add_col(__view_history_link(match.submission1) + " - "+ offering_str_sub1+" - "+ str(match.score1)+"%")
    row += add_col("<a href='"+view_moss_result_url(match)+"' target='_blank'>details</a>")
    row += "</tr>"
    return literal(row)

def filter_moss_matches_to_limit_per_assignment(matches, max_matches_per_assignment):
    if max_matches_per_assignment < 1:
        return matches
    
    matches.sort()
    matches.reverse()
    assignments_dict = {}
    
    def moss_match_to_dict_key(match):
        analysis = match.mossAnalysis.analysis
        assignment = analysis.assignment
        return assignment.course.name + " " + assignment.name
    
    for match in matches:
        assignments_dict[moss_match_to_dict_key(match)] = 0
        
    def filter_fun(match):
        assignments_dict[moss_match_to_dict_key(match)] = assignments_dict[moss_match_to_dict_key(match)] + 1
        if assignments_dict[moss_match_to_dict_key(match)] <= max_matches_per_assignment:
            return True
        return False
    
    return filter(filter_fun, matches)
