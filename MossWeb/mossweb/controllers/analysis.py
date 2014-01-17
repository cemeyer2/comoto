import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to
from pylons import config
from pylons.decorators import validate
from pylons.decorators.rest import restrict

from mossweb.lib.base import BaseController, render
from mossweb.lib import helpers as h
from mossweb.lib import analysis_helpers
from mossweb.model.model import FileSet, Course, Assignment, BaseFileSet, SolutionFileSet, StaticMossGraph
from mossweb.model import Session
from mossweb.lib.access import check_course_access, check_fileset_access, check_assignment_access
from mossweb.lib.static_graph_generator import StaticGraphProcessor

import shutil
import datetime
import os
import formencode

from mossweb.lib.decorators import require_enabled_user


log = logging.getLogger(__name__)

class NewAssignmentForm(formencode.Schema):
    allow_extra_fields = True
    filter_extra_fields = True
    name = formencode.validators.String(not_empty=True)

class AnalysisController(BaseController):

    @require_enabled_user()
    def __before__(self, controller, action):
        pass

    def create(self):
        c.user = h.get_user(request.environ)
        return render("/derived/analysis/create/select_course.html")
    
    def select_filesets(self, id=None):
        if id is None:
            abort(404)
        check_course_access(id)
        course = h.get_object_or_404(Course, id=id)
        c.course = course
        return render("/derived/analysis/create/select_filesets.html")
    
    def select_base_filesets(self):
        fileset_ids = analysis_helpers.fileset_id_string_to_id_list(request.params['filesets'])
        c.fileset_ids = request.params['filesets'] #comma separated list
        if len(fileset_ids) == 0:
            abort(500) #need to do something better here when a user selects no filesets
        c.course = h.get_object_or_404(FileSet, id=fileset_ids[0]).course
        check_course_access(c.course.id)
        return render("/derived/analysis/create/select_base_filesets.html")
    
    def create_assignment(self):
#        if id is None:
#            abort(404)
        fileset_ids = analysis_helpers.fileset_id_string_to_id_list(request.params['filesets'])
        filesets = FileSet.query.filter(FileSet.id.in_(fileset_ids)).all()
        
        base_fileset_ids = analysis_helpers.fileset_id_string_to_id_list(request.params['base_filesets'])
        base_filesets = BaseFileSet.query.filter(BaseFileSet.id.in_(base_fileset_ids)).all()
        
#        if len(filesets) == 0:
#            response.status_int = 302
#            response.headers['location'] = h.url_for(controller='analysis', action='select_filesets', id=id)
#            return "Moved temporarily"
        
        check_fileset_access(filesets)
        check_fileset_access(base_filesets) #could have done list.extend() here, but didnt want to modify either of the two original lists
        c.filesets = filesets
        c.base_filesets = base_filesets
        c.fileset_ids = request.params['filesets']
        c.base_fileset_ids = request.params['base_filesets']
        
        return render("/derived/analysis/create/create_assignment.html")
    
    #@restrict('POST')
    #@validate(schema=NewAssignmentForm(), form='create_assignment', file)
    def select_type(self):
        fileset_ids = analysis_helpers.fileset_id_string_to_id_list(request.params['filesets'])
        filesets = FileSet.query.filter(FileSet.id.in_(fileset_ids)).all()
        base_fileset_ids = analysis_helpers.fileset_id_string_to_id_list(request.params['base_filesets'])
        base_filesets = BaseFileSet.query.filter(BaseFileSet.id.in_(base_fileset_ids)).all()
        
        all_filesets = []
        all_filesets.extend(filesets)
        all_filesets.extend(base_filesets)
        check_fileset_access(all_filesets)
        
        name = request.params['name']
        language = request.params['language']
        assignment = Assignment()
        assignment.name = name
        assignment.language = language
        assignment.filesets = all_filesets
        
        assignment.course = filesets[0].offering.course
        c.assignment = assignment
        c.filesets = filesets
        c.fileset_ids = fileset_ids
        c.base_filesets = base_filesets
        c.base_fileset_ids = base_fileset_ids
        for fileset in all_filesets:
            fileset.assignments.append(assignment)
        Session.commit()
        return render("/derived/analysis/create/select_type.html")
    
    def moss_options(self, id=None):
        if id is None:
            abort(404)
        c.assignment = h.get_object_or_404(Assignment,id=id)
        check_assignment_access(c.assignment)
        c.moss_max_matches = 500
        c.deep_solution_choices = map(lambda fileset: (fileset.id,str(fileset.name) + " - " + fileset.offering.to_str()), filter(lambda f: f.row_type == 'fileset', c.assignment.filesets) )
        c.deep_solution_choices.insert(0, (-1, "None"))
        can_do_deep_solution = False
        total_submissions = 0
        for fs in c.assignment.filesets:
            if fs.row_type == 'solutionfileset':
                can_do_deep_solution = True
            elif fs.row_type == 'fileset':
                total_submissions = total_submissions + len(fs.submissions)
        c.can_do_deep_solution = can_do_deep_solution
        c.moss_repeat_options = range(1,101,1)
        c.moss_repeat_options.insert(0, total_submissions*total_submissions)
        c.moss_repeat_count = total_submissions*total_submissions
        
        return render("/derived/analysis/create/moss/moss_options.html")
        
    
    def moss_analysis(self):
        assignment_id = request.params['assignment_id']
        moss_repeat_count = request.params["moss_repeat_count"]
        moss_max_matches = request.params["moss_max_matches"]
        assignment = h.get_object_or_404(Assignment, id=assignment_id)
        check_assignment_access(assignment)
        analysis = analysis_helpers.do_moss(assignment, moss_repeat_count, moss_max_matches)
        analysis.timestamp = datetime.datetime.today()
        Session.commit()
        analysis_helpers.calculate_moss_matches(assignment)
        Session.commit()
        c.assignment = assignment
        session['analysis_status'] = "Generating histogram"
        session.save()
        session.persist()
        h.generate_histogram(assignment, "Original Histogram")
        session['analysis_status'] = ''
        session.save()
        session.persist()
        if request.params.has_key("deep_solution") and int(request.params['deep_solution']) != -1:
            deep_fs_id = int(request.params['deep_solution'])
            deep_fs = h.get_object_or_404(FileSet, id=deep_fs_id)
            solution_filesets = []
            base_filesets = []
            for fs in assignment.filesets:
                if fs.row_type == 'solutionfileset':
                    solution_filesets.append(fs)
                elif fs.row_type == 'basefileset':
                    base_filesets.append(fs)
            analysis_helpers.do_moss_deep_solution(assignment, deep_fs, solution_filesets, base_filesets)
        
        #prevents reposting form data
        return redirect_to(controller='view_analysis', action='list')
        
    def moss_complete(self):
        return render("/derived/analysis/create/moss/complete.html")
    
    def status(self):
        from pprint import pformat
        log.debug(pformat(session))
        if session.has_key('analysis_status'):
            return session['analysis_status']
        return ""
    
    def generate_static_graph(self, id):
        if id is None:
            abort(404)
        assignment = h.get_object_or_404(Assignment, id=id)
        check_assignment_access(assignment)
        c.assignment = assignment
        singleton = StaticGraphProcessor()
        c.queue_depth = singleton.get_number_of_graphs_in_queue()
        return render("/derived/analysis/create/generate_static_graph_facebox.html")
    
    def do_generate_static_graph(self, id):
        if id is None:
            abort(404)
        assignment = h.get_object_or_404(Assignment, id=id)
        check_assignment_access(assignment)
        threshold = int(request.params['threshold'])
        includeSolution = bool(int(request.params['includeSolution']))
        anonymize = bool(int(request.params['anonymize']))
        singletons = bool(int(request.params['singletons']))
        layoutEngine = request.params['layoutEngine']
        singleton = StaticGraphProcessor()
        singleton.add_static_graph_to_queue(assignment, threshold=threshold, includeSolution=includeSolution,anonymize=anonymize,singletons=singletons,layoutEngine=layoutEngine)
        queue_depth = singleton.get_number_of_graphs_in_queue()
        return h.literal("Request submitted successfully. There are now "+str(queue_depth)+" graphs waiting in the processing queue")
        
