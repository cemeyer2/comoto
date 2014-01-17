import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from mossweb.lib.base import BaseController, render

from mossweb.lib import helpers as h
from mossweb.lib import analysis_helpers as ah
from mossweb.lib.access import check_assignment_access, check_student_access
from mossweb.model.model import *
from mossweb.model import Session
import re
from mossweb.lib.decorators import require_enabled_user

import os, sys

log = logging.getLogger(__name__)

class ViewAnalysisController(BaseController):

    @require_enabled_user()
    def __before__(self, controller, action):
        pass

    def list(self):
        user = h.get_user(request.environ)
        c.user = user
        for course in user.courses:
            course.assignments.sort()
        return render("/derived/analysis/view/list.html")
    
    def delete(self, id=None):
        if id is None:
            abort(404)
        assignment = h.get_object_or_404(Assignment, id=id)
        assignment.filesets = [] #so we dont delete the filesets
        assignment.delete()
        Session.commit()
        redirect_to(controller="view_analysis", action="list")
    
    def view(self, id=None):
        if id is None:
            abort(404)
        assignment = h.get_object_or_404(Assignment, id=id)
        log.debug("PAST CHECK")
        filter_thresh = 0
        if request.params.has_key("filter"):
            filter_thresh = int(request.params['filter'])
        c.filter = filter_thresh
        single_student_max = -1
        if request.params.has_key("single_student_max"):
            single_student_max = int(request.params["single_student_max"])
        c.single_student_max = single_student_max
        single_student_max_upper_bound = sys.maxint
        if request.params.has_key("single_student_max_upper_bound"):
            single_student_max_upper_bound = int(request.params["single_student_max_upper_bound"])
        if single_student_max_upper_bound < single_student_max:
            single_student_max_upper_bound = single_student_max
        c.single_student_max_upper_bound = single_student_max_upper_bound
        check_assignment_access(assignment)
        c.assignment = assignment
        analysis = assignment.analysis
        base = os.path.basename(analysis.webDirectory)
        c.link_base = h.url_for('/moss_analysis/'+str(base)+'/')
        matches = assignment.analysis.mossAnalysis.matches
        matches = filter(lambda match: match.hidden == False, matches)
        c.offerings = ah.get_offerings_for_analysis(analysis)
        matches = h.filter_moss_matches_to_minimum_score(matches, filter_thresh)
        matches.sort()
        matches.reverse()
        c.matches = matches
        c.solutionMatches = filter(lambda x: isinstance(x.submission1, SolutionSubmission) or isinstance(x.submission2, SolutionSubmission), c.matches)
        c.crossSemesterMatches = filter(lambda x: isinstance(x.submission1, StudentSubmission) and isinstance(x.submission2, StudentSubmission) and x.submission1.offering.id != x.submission2.offering.id, c.matches)
        c.sameSemesterMatches = filter(lambda x: isinstance(x.submission1, StudentSubmission) and isinstance(x.submission2, StudentSubmission) and x.submission1.offering.id == x.submission2.offering.id, c.matches)
        
        if single_student_max > 0:
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
                    if netid_dict[netid1] <= single_student_max or netid_dict[netid2] <= single_student_max:
                        if netid_dict[netid1] > single_student_max_upper_bound or netid_dict[netid2] > single_student_max_upper_bound:
                            return False
                        return True
                    else:
                        return False
                return True
            #matches = filter(filter_fun, matches)
            c.crossSemesterMatches = filter(filter_fun, c.crossSemesterMatches)
            c.sameSemesterMatches = filter(filter_fun, c.sameSemesterMatches)
        c.staticMossGraphs = StaticMossGraph.query.filter(StaticMossGraph.assignment==assignment).filter(StaticMossGraph.isComplete==True).all()
        return render("/derived/analysis/view/view.html")
    
    def prune(self):
        assignment_id = request.params['assignment_id']
        offering_id = request.params['offering_id']
        assignment = h.get_object_or_404(Assignment, id=assignment_id)
        offering = h.get_object_or_404(Offering, id=offering_id)
        check_assignment_access(assignment)
        mossAnalysis = assignment.analysis.mossAnalysis
        from mossweb.lib.analysis_helpers import prune_moss_analysis
        prune_moss_analysis(mossAnalysis, offering)
        h.generate_histogram(assignment, "Pruned Histogram")
        return redirect_to(controller="view_analysis", action="view", id=assignment.id)
        
        
    def view_moss_result(self, id=None):
        if id is None:
            abort(404)
        file = h.get_object_or_404(MossReportFile, id=id)
        check_assignment_access(file.mossReport.report.assignment)
        content = file.content
        extension = file.name.split('.')[-1]
        log.debug("processing file: "+file.name)
        log.debug("extension: "+extension)
                
        linksRegex = re.compile('match.{3,10}(\.html)', re.DOTALL)
        
        links = linksRegex.finditer(content)
        old_links = []
        for link in links:
            start = link.start()
            end = link.end()
            old_text = content[start:end]
            log.debug("found link: "+old_text)
            old_links.append(old_text)
        for old_link in old_links:
            old_link2 = old_link.replace("html",extension)
            log.debug("searching for moss report file with name="+old_link2)
            linked_file = h.get_object_or_404(MossReportFile, name=old_link2, mossReport=file.mossReport)
            new_link = h.url_for(controller="view_analysis", action="view_moss_result", id=linked_file.id)
            content = content.replace(old_link, new_link)
        imagesRegex = re.compile('\.\./bitmaps/.*?\.gif')
        images = imagesRegex.finditer(content)
        old_images = []
        for image in images:
            start = image.start()
            end = image.end()
            old_text = content[start:end]
            old_images.append(old_text)
        for old_image in old_images:
            image_file = old_image[11:]
            url = h.url_for('/moss_bitmaps/'+str(image_file))
            content = content.replace(old_image, url)
        return content
    
    def email_students(self, id):
        #student_ids_str = request.params['student_ids']
        student_ids_str = id
        student_ids = ah.fileset_id_string_to_id_list(student_ids_str)
        students = Student.query.filter(Student.id.in_(student_ids)).all()
        c.students = students
        c.student_ids_str = student_ids_str
        if request.params.has_key('aid'):
            c.assignment_id = request.params['aid']
        return render("/derived/analysis/view/email.html")
    
    def email_students_ajax(self, id):
        #student_ids_str = request.params['student_ids']
        student_ids_str = id
        student_ids = ah.fileset_id_string_to_id_list(student_ids_str)
        students = Student.query.filter(Student.id.in_(student_ids)).all()
        c.students = students
        c.student_ids_str = student_ids_str
        if request.params.has_key('aid'):
            c.assignment_id = request.params['aid']
        return render("/derived/analysis/view/email_facebox.html")
    
    def do_email_students(self):
        log.debug(str(request.params))
        user = h.get_user(request.environ)
        student_ids_str = request.params['student_ids']
        student_ids = ah.fileset_id_string_to_id_list(student_ids_str)
        students = Student.query.filter(Student.id.in_(student_ids)).all()
        students = filter(lambda student: request.params.has_key(str(student.id)), students)
        for student in students:
            check_student_access(student)
        subject = request.params['subject']
        body = request.params['body']
        from_addr = (user.givenName+" "+user.surName,user.name + '@illinois.edu')
        reply_to = user.name + '@illinois.edu'
        to_addrs = map(lambda student: (student.displayName, student.netid + "@illinois.edu"), students)
        from turbomail import Message
        message = Message()
        message.subject = subject
        message.plain = body
        message.author = from_addr
        message.reply_to = reply_to
        message.to = to_addrs
        message.cc = from_addr
        message.send()
        if request.params.has_key('assignment_id'):
            return redirect_to(controller='view_analysis', action='view', id=request.params['assignment_id'])
        else:
            return redirect_to(controller='view_analysis', action='list')
        
    def do_email_students_ajax(self):
        log.debug(str(request.params))
        user = h.get_user(request.environ)
        student_ids_str = request.params['student_ids']
        student_ids = ah.fileset_id_string_to_id_list(student_ids_str)
        students = Student.query.filter(Student.id.in_(student_ids)).all()
        students = filter(lambda student: request.params.has_key(str(student.id)), students)
        for student in students:
            check_student_access(student)
        subject = request.params['subject']
        body = request.params['body']
        from_addr = (user.givenName+" "+user.surName,user.name + '@illinois.edu')
        reply_to = user.name + '@illinois.edu'
        to_addrs = map(lambda student: (student.displayName, student.netid + "@illinois.edu"), students)
        from turbomail import Message
        message = Message()
        message.subject = subject
        message.plain = body
        message.author = from_addr
        message.reply_to = reply_to
        message.to = to_addrs
        message.cc = from_addr
        message.send()
        return "Message Sent Successfully"
    
    def view_static_graph(self,id):
        if id is None:
            abort(404)
        graph_id = int(id.split(".")[0]) #we append .gif to the id in the template to make web browsers happier when saving the images
        graph = h.get_object_or_404(StaticMossGraph, id=graph_id)
        check_assignment_access(graph.assignment)
        response.content_type = "image/png"
        response.content_length = len(graph.imageData)
        f = open("/tmp/graph.png", "w")
        f.write(graph.imageData)
        f.close()
        return graph.imageData
    
    def view_static_graph_thumbnail(self,id):
        if id is None:
            abort(404)
        graph_id = int(id.split(".")[0]) #we append .gif to the id in the template to make web browsers happier when saving the images
        graph = h.get_object_or_404(StaticMossGraph, id=graph_id)
        check_assignment_access(graph.assignment)
        response.content_type = "image/png"
        response.content_length = len(graph.thumbnailData)
        return graph.thumbnailData
    
    def view_static_graph_medium(self,id):
        if id is None:
            abort(404)
        graph_id = int(id.split(".")[0]) #we append .gif to the id in the template to make web browsers happier when saving the images
        graph = h.get_object_or_404(StaticMossGraph, id=graph_id)
        check_assignment_access(graph.assignment)
        response.content_type = "image/png"
        response.content_length = len(graph.mediumData)
        return graph.mediumData
    
    def export_moss_match(self, id):
        if id is None:
            abort(404)
        match = h.get_object_or_404(MossMatch, id=id)
        check_assignment_access(match.mossAnalysis.analysis.assignment)
        assignment = match.mossAnalysis.analysis.assignment
        report = assignment.report.mossReport
        index_file = h.get_object_or_404(MossReportFile, name=match.link, mossReport=report)
        linksRegex = re.compile('match.{3,10}(\.html)', re.DOTALL) 
        links = linksRegex.finditer(index_file.content)
        files = [index_file]
        for link in links:
            start = link.start()
            end = link.end()
            filename = index_file.content[start:end]
            file = h.get_object_or_404(MossReportFile, name=filename, mossReport=report)
            if file not in files:
                files.append(file)
        import zipfile, os
        from tempfile import mkstemp
        tempzipfile = mkstemp(".zip")[1]
        zip = zipfile.ZipFile(tempzipfile, "w")
        for file in files:
            (fp, tempfile) = mkstemp(file.name)
            fp = os.fdopen(fp)
            fp.close()
            fp = open(tempfile, 'w')
            content = file.content
            if request.params.has_key('anonymize'):
                content = h.anonymize_file_content(file, match)
            fp.write(content)
            fp.close()
            zip.write(tempfile, file.name)
            os.remove(tempfile)
        zip.close()
        fp = open(tempzipfile)
        zipcontent = fp.read()
        fp.close()
        os.remove(tempzipfile)
        response.content_type = "application/zip"
        response.headerlist.append(("Content-Disposition", "inline; filename=\"mossmatch.zip\""))
        return zipcontent        
        
    def export_moss_match_ajax(self, id):
        c.match_id = id
        return render("/derived/analysis/view/export_facebox.html")