import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from mossweb.lib import helpers as h
from mossweb.lib.base import BaseController, render
from mossweb.model.model import *
from mossweb.model import Session
from mossweb.lib.access import check_fileset_access, check_file_access
from sqlalchemy import or_
from mossweb.lib.decorators import require_enabled_user

log = logging.getLogger(__name__)

class FilesetController(BaseController):

    @require_enabled_user()
    def __before__(self, controller, action):
        pass

    def list_filesets(self):
        c.user = h.get_user(request.environ)
        c.courses = c.user.courses
        for course in c.courses:
            course.offerings.sort()
        return render("/derived/fileset/list_filesets.html")
    
    def list_fileset(self, id=None):
        if id is None:
            abort(404)
        c.fileset = h.get_object_or_404(FileSet, id=id)
        check_fileset_access([c.fileset])
        if not c.fileset.isSolutionSet:
            c.submissions = c.fileset.submissions.sort(lambda x,y: cmp(x.student.netid, y.student.netid))
        return render("/derived/fileset/list_fileset.html")
    
    def view_file(self, id=None):
        if id is None:
            abort(404)
        file = h.get_object_or_404(SubmissionFile, id=id)
        check_file_access(file)
        (formatted_text, filename, mime) = h.format_file(file, "html")
        c.formatted_text = formatted_text
        c.file = file
        
        return render("/derived/fileset/view_file.html")

    def download_file_ajax(self, id=None):
        if id is None:
            abort(404)
        file = h.get_object_or_404(SubmissionFile, id=id)
        check_file_access(file)
        c.file = file
        return render("/derived/fileset/download_file_ajax.html")        

    def download_file(self, id=None):
        if id is None:
            abort(404)
        file = h.get_object_or_404(SubmissionFile, id=id)
        check_file_access(file)
        format = "raw"
        if request.params.has_key("format"):
            format = request.params["format"]
        (content, filename, mime) = h.format_file(file, format)
        response.content_length = len(content)
        #this line causes the save dialog to show the name of the file rather than its id (which it would have gotten from the url)
        response.headerlist.append(("Content-Disposition", "attachment; filename=\""+filename+"\""))
        response.content_type = mime
        return content
    
    def download_submission_ajax(self, id=None):
        if id is None:
            abort(404)
        sub = h.get_object_or_404(Submission, id=id)
        check_fileset_access([sub.fileset])
        c.sub = sub
        return render("/derived/fileset/download_submission_ajax.html")  
    
    def download_submission(self, id=None):
        if id is None:
            abort(404)
        sub = h.get_object_or_404(Submission, id=id)
        check_fileset_access([sub.fileset])
        format = "raw"
        if request.params.has_key("format"):
            format = request.params["format"]
        import zipfile, os
        from tempfile import mkstemp
        tempzipfile = mkstemp(".zip")[1]
        zip = zipfile.ZipFile(tempzipfile, "w")
        for file in sub.submissionFiles:
            (content, filename, mime) = h.format_file(file, format)
            (fp, tempfile) = mkstemp(filename)
            fp = os.fdopen(fp)
            fp.close()
            fp = open(tempfile, 'w')
            fp.write(content)
            fp.close()
            zip.write(tempfile, filename)
            os.remove(tempfile)
        zip.close()
        fp = open(tempzipfile)
        zipcontent = fp.read()
        fp.close()
        os.remove(tempzipfile)
        response.content_type = "application/zip"
        from mossweb.lib.moss_helpers import submission_to_str
        #this line causes the save dialog to show the name of the file rather than its id (which it would have gotten from the url)
        response.headerlist.append(("Content-Disposition", "attachment; filename=\""+submission_to_str(sub)+".zip\""))
        return zipcontent

    def download_fileset_ajax(self, id=None):
        if id is None:
            abort(404)
        fileset = h.get_object_or_404(FileSet, id=id)
        check_fileset_access([fileset])
        c.fileset = fileset
        return render("/derived/fileset/download_fileset_ajax.html")  

    def download_fileset(self, id=None):
        if id is None:
            abort(404)
        fileset = h.get_object_or_404(FileSet, id=id)
        check_fileset_access([fileset])
        format = "raw"
        if request.params.has_key("format"):
            format = request.params["format"]
        import zipfile, os
        from tempfile import mkstemp, mkdtemp
        from mossweb.lib.moss_helpers import submission_to_download_str
        tempzipfile = mkstemp(".zip")[1]
        zip = zipfile.ZipFile(tempzipfile, "w")
        for submission in fileset.submissions:
            for file in submission.submissionFiles:
                (content, filename, mime) = h.format_file(file, format)
                (fp, tempfile) = mkstemp(filename)
                fp =os. fdopen(fp)
                fp.close()
                fp = open(tempfile, 'w')
                fp.write(content)
                fp.close()
                zip.write(tempfile, str(submission_to_download_str(submission)+"/"+filename))
                os.remove(tempfile)
        zip.close()
        fp = open(tempzipfile)
        zipcontent = fp.read()
        fp.close()
        os.remove(tempzipfile)
        response.content_type = "application/zip"
        #this line causes the save dialog to show the name of the file rather than its id (which it would have gotten from the url)
        response.headerlist.append(("Content-Disposition", "attachment; filename=\""+fileset.name+".zip\""))
        return zipcontent
        
    def remove_fileset(self, id=None):
        if id is None:
            abort(404)
        fileset = h.get_object_or_404(FileSet, id=id)
        check_fileset_access([fileset])
        for assignment in fileset.assignments:
            try:    
                if assignment.analysis is not None:
                    if assignment.analysis.mossAnalysis is not None:
                        Session.delete(assignment.analysis.mossAnalysis)
                    Session.delete(assignment.analysis)
                Session.delete(assignment)
            except:
                pass
        Session.delete(fileset)
        Session.commit()
        redirect_to(controller="fileset", action="list_filesets")
    
    def remove_submission(self, id=None):
        if id is None:
            abort(404)
        sub = h.get_object_or_404(Submission, id=id)
        check_fileset_access([sub.fileset])
        f_id = sub.fileset.id
        matches = MossMatch.query.filter_by(submission1=sub).all()
        matches.extend(MossMatch.query.filter_by(submission2=sub).all())
        for match in matches:
            Session.delete(match)
        Session.delete(sub)
        Session.commit()
        redirect_to(controller='fileset', action='list_fileset', id=f_id)
    
    def remove_file(self, id=None):
        if id is None:
            abort(404)
        sub = h.get_object_or_404(SubmissionFile, id=id)
        check_fileset_access([sub.submission.fileset])
        f_id = sub.submission.fileset.id
        Session.delete(sub)
        Session.commit()
        redirect_to(controller='fileset', action='list_fileset', id=f_id)

        
