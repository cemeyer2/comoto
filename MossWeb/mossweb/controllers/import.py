import logging


from pylons.controllers.util import abort, redirect_to

from mossweb.lib.base import BaseController, render

from mossweb.lib import helpers as h
from mossweb.lib import import_helpers

from mossweb.model.model import *
from pylons import request, response, session, tmpl_context as c
from mossweb.model import Session
import shutil
import os
from pylons import config
from tempfile import mkdtemp
import zipfile
from zipfile import ZipFile
import tarfile
from tarfile import TarFile
import pysvn
from mossweb.lib.access import check_course_access, check_offering_access, check_fileset_access
from webhelpers.html.tags import HTML
import formencode
from formencode import htmlfill
from pylons.decorators import validate, jsonify
from pylons.decorators.rest import restrict
import re
import time
from mossweb.lib.decorators import require_enabled_user

log = logging.getLogger(__name__)

class ValidCourse(formencode.validators.FancyValidator):
    def _to_python(self, value, state):
        value = formencode.validators.Int().to_python(value, state)
        course = Course.get_by(id=value)
        if not course:
            raise formencode.Invalid("Invalid course specified", value, state)
        user = h.get_user(request.environ)
        if course not in user.courses:
            raise formencode.Invalid("You do not have access for the course you specified", value, state)
        return value

class ValidOffering(formencode.validators.FancyValidator):
    def _to_python(self, value, state):
        value = formencode.validators.Int().to_python(value, state)
        if int(request.params['is_solution']) == 1:
            return value
        offering = Offering.get_by(id=value)
        if not offering:
            raise formencode.Invalid("Invalid offering specified", value, state)
        user = h.get_user(request.environ)
        if offering.course not in user.courses:
            raise formencode.Invalid("You do not have access for the offering you specified", value, state)
        return value
    
class ValidSVNURL(formencode.validators.FancyValidator):
    def _to_python(self, value, state):
        type = request.params['type']
        if type == 'archive':
            return value
        value = formencode.validators.URL(add_http=True, check_exists=True, require_tld=False).to_python(value, state)
        return value

class ImportForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    fileset_name = formencode.validators.String(not_empty=True)
    course_id = ValidCourse(not_empty=True)
    is_solution = formencode.validators.Bool()
    offering_id = ValidOffering()
    svn_url = ValidSVNURL()
    svn_subdir = formencode.validators.String()
    svn_username = formencode.validators.String()
    svn_password = formencode.validators.String()

class ImportController(BaseController):

    @require_enabled_user()
    def __before__(self, controller, action):
        pass

    #deprecated
    def start(self):
        c.user = h.get_user(request.environ)
        return render("/derived/import/select_course.html")
    
    def begin(self):
        c.user = h.get_user(request.environ)
        return render("/derived/import/import_form.html")
    
    def get_offerings_for_course(self, id=None):
        if id is None:
            return ""
        check_course_access(id)
        course = h.get_object_or_404(Course, id=id)
        offerings = course.offerings
        offerings.sort()
        offerings.reverse()
        result = []
        for offering in offerings:
            result.append(HTML.option(offering.semester.to_str(), value=offering.id))
        return u''.join(result)
    
    @validate(schema=ImportForm(), form='start2')
    def filter_files(self):
        fileset_name = request.params["fileset_name"]
        unique_id = request.params['unique_id']
        course = h.get_object_or_404(Course, id=request.params["course_id"])
        check_course_access(course.id)
        #is_solution = bool(int(request.params["is_solution"]))
        offering = h.get_object_or_404(Offering, id=request.params["offering_id"])
        semester = offering.semester
        student_fileset = 0
        solution_fileset = 1
        base_fileset = 2
        fileset_type = student_fileset
        if isinstance(semester, SolutionSemester):
            fileset_type = solution_fileset
        elif isinstance(semester, BaseSemester):
            fileset_type = base_fileset
        type = request.params["type"]
        if type == "svn":
            svnroot = str(request.params["svn_url"])
            subdir = str(request.params["svn_subdir"])
            username = str(request.params["svn_username"])
            password = str(request.params["svn_password"])
            rev_time = time.strptime(str(request.params['svn_rev_time']), "%Y-%m-%d %H:%M:%S")
            exported_path = h.svn_export(svnroot, username, password, subdir, rev_time, fileset_type>0,unique_id)
            h.update_session('import_status', "Post-processing files", unique_id)
            fileset = None
            if fileset_type == student_fileset:
                fileset = FileSet()
            elif fileset_type == solution_fileset:
                fileset = SolutionFileSet()
                fileset.isSolutionSet = True
            elif fileset_type == base_fileset:
                fileset = BaseFileSet()
            fileset.name = fileset_name
            fileset.subdir = subdir
            fileset.tempDir = exported_path
            fileset.course = course
            fileset.offering = offering
            fileset.isComplete = False
            c.fileset = fileset
            files = h.lsdir(fileset.tempDir)
            files = map(lambda x: x[len(fileset.tempDir)+1:], files) #chop off temp dir from names
            files.sort()
            c.files = files
        if type == "archive":
            h.update_session('import_status', "Processing archive file",unique_id)
            subdir = request.params["archive_subdir"]
            myfile = request.POST['file']
            download_path = mkdtemp()
            path =  os.path.join(download_path, myfile.filename.replace(os.sep, '_'))        
            permanent_file = open(path,'wb')
            shutil.copyfileobj(myfile.file, permanent_file)
            myfile.file.close()
            permanent_file.close()
            extracted_directory_path = mkdtemp()
            h.update_session('import_status', "Extracting archive file",unique_id)
            if zipfile.is_zipfile(path):
                file = ZipFile(path, 'r')
                h.extract_zip(file, extracted_directory_path)
            if tarfile.is_tarfile(path):
                file = TarFile.open(path, 'r')
                #file.extractall(extracted_directory_path) removed for python 2.4 compat
                for member in file.getmembers():
                    file.extract(member, extracted_directory_path)
            h.update_session('import_status', "Post-processing files",unique_id)
            if fileset_type == student_fileset:
                fileset = FileSet()
            elif fileset_type == solution_fileset:
                fileset = SolutionFileSet()
                fileset.isSolutionSet = True
            elif fileset_type == base_fileset:
                fileset = BaseFileSet()
            fileset.name = fileset_name
            fileset.subdir = subdir
            fileset.tempDir = extracted_directory_path
            fileset.course = course
            fileset.offering = offering
            fileset.isComplete = False
            c.fileset = fileset
            files = h.lsdir(fileset.tempDir)
            files = map(lambda x: x[len(fileset.tempDir)+1:], files) #chop off temp dir from names
            files.sort()
            c.files = files
            shutil.rmtree(download_path)
        Session.commit()
        
        
        unique_files_dict = {}
        for filepath in c.files:
            filename = filepath.split("/")[-1]
            if not unique_files_dict.has_key(filename):
                unique_files_dict[filename] = 0
            else:
                unique_files_dict[filename] = unique_files_dict[filename] + 1
        
        c.unique_files = sorted(unique_files_dict.keys(), cmp=lambda x,y: cmp(unique_files_dict[x], unique_files_dict[y]), reverse=True)
        c.unique_files.insert(0, "None")
        
        h.del_from_session('import_status', unique_id)
        session.save()
        return render("/derived/import/filter_files.html")
    
    def import_files(self):
        fileset = h.get_object_or_404(FileSet, id=request.params['fileset_id'])
        check_fileset_access([fileset])
        pattern = request.params['regex']
        meta_file_name = request.params['meta']
        #log.debug("PATTERN: "+pattern)
        regex = re.compile(pattern)
        dirlist = h.lsdir(fileset.tempDir)
        #log.debug("DIRLIST: "+str(dirlist))
        files = []
        for file in dirlist:
            if regex.search(file) is not None:
                files.append(file)
        import_helpers.import_files(fileset, files, meta_file_name)
        shutil.rmtree(fileset.tempDir) #clean up after ourselves, we save disk space that way
        Session.commit()
        if fileset.row_type == 'fileset':
            regex_str = h.build_parse_partners_regex(fileset)
            for submission in fileset.submissions:
                h.parse_partners(submission, regex_str)
        redirect_to(controller="fileset", action="list_filesets")
    
    @jsonify
    def try_svn_login(self):
        username = str(request.params["username"])
        password = str(request.params["password"])
        url = str(request.params["url"])
        logged_in = h.try_svn_login(username, password, url)
        return {"result":logged_in}
    
    def status(self, id):
        return h.get_from_session('import_status', id)
