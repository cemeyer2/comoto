import logging
from mossweb.controllers.api import ApiController
from mossweb.lib.decorators import require_enabled_user
from pylons import request, response, session, tmpl_context as c
from mossweb.lib import helpers as h
from mossweb.model.model import Assignment
from mossweb.lib.base import BaseController, render
from pylons.decorators import jsonify

log = logging.getLogger(__name__)

class VizController(BaseController):

    def __init__(self):

        # Get a handle on the API controller
        self.apiController = ApiController()
        super(VizController, self).__init__()

    @require_enabled_user()
    def __before__(self):
        pass

    @jsonify
    def getCourseData(self):
        """Wrapper around getCourses and getAssignments API controller calls that returns the dictionary of all courses
        accessible to the current user, populated with all available assignment data for each course"""

        # Get the list of courses, offerings, assignments,filesets, and additional class data available from the API
        courses = self.apiController.getCourses(True)

        # Get the assignment data for each course
        for course in courses:
            course['assignments'] = self.apiController.getAssignments(course['id'])

        return courses


    @jsonify
    def getMatchesAndSubmissions(self):
        """Wrapper around API controller that gets all match & submission data for an assignment, given its id"""

        # Get the analysis & assignment data for this id
        assignmentId = str(request.params["assignmentId"])
        assignment = self.apiController.getAssignment(int(assignmentId))
        analysis = self.apiController.getAnalysis(assignment['analysis_id'])

        # Get the MOSS matches for this assignment
        mossAnalysis = self.apiController.getMossAnalysis(analysis['moss_analysis_id'], True)
        sameSemesterMatches = mossAnalysis['same_semester_matches']
        solutionMatches = mossAnalysis['solution_matches']
        crossSemesterMatches = mossAnalysis['cross_semester_matches']
        matches = {
            'sameSemesterMatches': sameSemesterMatches,
            'solutionMatches': solutionMatches,
            'crossSemesterMatches': crossSemesterMatches
        }

        # Get the submissions for this semester
        fileSetIds = assignment['fileset_ids']
	#fileSets = self.apiController.getFileSets(fileSetIds, True)
        submissions = {}
        for fileSetId in fileSetIds:
            fileSet = self.apiController.getFileSet(fileSetId, True)
            for submission in fileSet['submissions']:
                submissions[submission['id']] = submission

        # Encode the submissions & matches to send them back
        return {
            'matches' : matches,
            'submissions' : submissions
        }
        
    @jsonify
    def getSubmissionsForFileset(self):
        submissions = {}
        fileSet = self.apiController.getFileSet(int(request.params['filesetId']), True)
        for submission in fileSet['submissions']:
            submissions[submission['id']] = submission
        return submissions
    
    @jsonify
    def getMatches(self):
        """Wrapper around API controller that gets all match & submission data for an assignment, given its id"""

        # Get the analysis & assignment data for this id
        assignmentId = str(request.params["assignmentId"])
        assignment = self.apiController.getAssignment(int(assignmentId))
        analysis = self.apiController.getAnalysis(assignment['analysis_id'])

        # Get the MOSS matches for this assignment
        mossAnalysis = self.apiController.getMossAnalysis(analysis['moss_analysis_id'], True)
        sameSemesterMatches = mossAnalysis['same_semester_matches']
        solutionMatches = mossAnalysis['solution_matches']
        crossSemesterMatches = mossAnalysis['cross_semester_matches']
        matches = {
            'sameSemesterMatches': sameSemesterMatches,
            'solutionMatches': solutionMatches,
            'crossSemesterMatches': crossSemesterMatches
        }


    def index(self, id=-1):
        offering_id = -1
        course_id = -1
        if id >= 0:
            assignment = h.get_object_or_404(Assignment, id=id)
            if assignment.analysis.mossAnalysis.prunedOffering is not None:
                offering_id = assignment.analysis.mossAnalysis.prunedOffering.id
                course_id = assignment.analysis.mossAnalysis.prunedOffering.course.id
        c.preload_assignment_id = id
        c.preload_offering_id = offering_id
        c.preload_course_id = course_id
        return render("/derived/viz/index.html")
    
    def export(self):
        svg = request.params["svg"]
        response.headerlist.append(("Content-Disposition", "attachment; filename=\"viz.svg\""))
        response.content_type = 'image/svg'
        return svg

