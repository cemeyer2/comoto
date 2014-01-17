from elixir import *
import sqlalchemy
import elixir
from sqlalchemy.schema import UniqueConstraint
import datetime
try:
    from sqlalchemy.databases.mysql import MSLongText, MSMediumBlob
except ImportError:
    from sqlalchemy.dialects.mysql.base import MSLongText, MSMediumBlob
from mossweb.model import Session
#from sqlalchemy.types import CLOB

elixir.options_defaults['table_options'] = dict(mysql_engine="InnoDB")

# http://www.sqlalchemy.org/trac/wiki/UsageRecipes/Enum
class Enum(sqlalchemy.types.TypeDecorator):
    impl = sqlalchemy.types.Unicode

    def __init__(self, values, empty_to_none=False, strict=False):
        """Emulate an Enum type.

        values:
            A list of valid values for this column
        empty_to_none:
            Optional, treat the empty string '' as None
        strict:
            Also insist that columns read from the database are in the
            list of valid values.  Note that, with strict=True, you won't
            be able to clean out bad data from the database through your
            code.
        """

        if values is None or len(values) is 0:
            raise AssertionError('Enum requires a list of values')
        self.empty_to_none = empty_to_none
        self.strict = strict
        self.values = values[:]

        # The length of the string/unicode column should be the longest string
        # in values
        size = max([len(v) for v in values if v is not None])
        super(Enum, self).__init__(size)        

    def process_bind_param(self, value, dialect):
        if self.empty_to_none and value is '':
            value = None
        if value not in self.values:
            raise AssertionError('"%s" not in Enum.values' % value)
        return value


    def process_result_value(self, value, dialect):
        if self.strict and value not in self.values:
            raise AssertionError('"%s" not in Enum.values' % value)
        return value

class User(elixir.Entity):
    name = elixir.Field(elixir.String(10), unique=True)
    superuser = elixir.Field(elixir.Boolean())
    courses = elixir.ManyToMany('Course')
    enabled = elixir.Field(elixir.Boolean(), default=True)
    requested_courses = elixir.Field(elixir.String(255)) #this should go into extraData
    givenName = elixir.Field(elixir.String(128))
    surName = elixir.Field(elixir.String(128))
    dn = elixir.Field(elixir.String(1024))
    staticMossGraphs = elixir.OneToMany('StaticMossGraph')
    staticJPlagGraphs = elixir.OneToMany('StaticJPlagGraph')
    emailTemplate = elixir.Field(MSLongText())
    extraData = elixir.OneToOne('ExtraData')
    
    
    def get_name(self):
        return self.givenName + " " + self.surName

    def __repr__(self):
        return "<user "+self.name+" superuser="+str(self.superuser)+" enabled="+str(self.enabled)+">"
    
    def __cmp__(self, other):
        if isinstance(other, User):
            return cmp(self.name, other.name)
        else:
            return cmp(self.__hash__(), other.__hash__())
    
class Semester(elixir.Entity):
    #season = elixir.Field(Enum([u'Spring', u'Summer', u'Fall'], strict=True),
    #                      primary_key=True)
    #year = elixir.Field(elixir.Integer(), primary_key=True)
    
    season = elixir.Field(Enum([u'Spring', u'Summer', u'Fall'], strict=True))
    year = elixir.Field(elixir.Integer())
    isSolution = elixir.Field(elixir.Boolean(), default=False)
    extraData = elixir.OneToOne('ExtraData')
    
    using_table_options(UniqueConstraint('season', 'year'))
    
    def to_str(self):
        return self.season+" "+str(self.year)

    def __repr__(self):
        return "<semester %s %d>" % (self.season, self.year)

    def __cmp__(self, other):
        if isinstance(other, Semester) or isinstance(other, SolutionSemester) or isinstance(other, BaseSemester):
            if self.isSolution:
                return -1
            if other.isSolution:
                return 1
            if self.year == other.year:
                seasons = [u'Spring', u'Summer', u'Fall']
                return cmp(seasons.index(self.season),
                           seasons.index(other.season))
            else:
                return cmp(self.year, other.year)
        else:
            return cmp(self.__hash__(), other.__hash__())
        
class SolutionSemester(Semester):
    elixir.using_options(inheritance='multi')
    def __repr__(self):
        return "<semester solution>"
    
    def to_str(self):
        return "Solution"

class BaseSemester(Semester):
    elixir.using_options(inheritance='multi')
    def __repr__(self):
        return "<semester base>"
    
    def to_str(self):
        return "Base Files"

class Course(elixir.Entity):
    name = elixir.Field(elixir.String(10), unique=True)
    offerings = elixir.OneToMany('Offering', cascade='all')
    assignments = elixir.OneToMany('Assignment', cascade='all')
    users = elixir.ManyToMany('User')
    filesets = elixir.OneToMany('FileSet')
    dn = elixir.Field(elixir.String(1024))
    extraData = elixir.OneToOne('ExtraData')

    def __repr__(self):
        return "<course %s>" % self.name
    
    def __cmp__(self, other):
        if isinstance(other, Course):
            return cmp(self.name, other.name)
        else:
            return cmp(self.__hash__(), other.__hash__())

class Offering(elixir.Entity):
    semester = elixir.ManyToOne('Semester')
    course = elixir.ManyToOne('Course')
    filesets = elixir.OneToMany('FileSet')
    dns = elixir.Field(PickleType(), default=[])
    extraData = elixir.OneToOne('ExtraData')
    prunedMossAnalyses = elixir.OneToMany('MossAnalysis')
    prunedJPlagAnalyses = elixir.OneToMany('JPlagAnalysis')
    students = elixir.ManyToMany('Student')
    
    using_table_options(UniqueConstraint('semester_id', 'course_id'))
    
    def to_str(self):
        return self.course.name + " "+ self.semester.to_str()
    
    def __repr__(self):
        return "<offering: %s in %s>" % (self.course.name, self.semester)
    
    def __cmp__(self, other):
        if isinstance(other, Offering):
            return cmp(self.semester, other.semester)
        else:
            return cmp(self.__hash__(), other.__hash__())

class Assignment(elixir.Entity):
    course = elixir.ManyToOne('Course')
    name = elixir.Field(elixir.String(1024))
    filesets = elixir.ManyToMany('FileSet', cascade='all')    
    language = elixir.Field(Enum(["c", "cc", "java", "ml", "ocaml", "ruby", "pascal", "ada", "lisp", "scheme", "haskell", "fortran", "ascii", "vhdl", "perl", "matlab", "python", "mips", "prolog", "spice", "vb", "csharp", "modula2", "a8086", "javascript", "plsql", "verilog", "tcl", "hc12", "asm", "java12", "java15", "java15dm", "scheme", "c/c++", "text", "char", "c#-1.2"], strict=True))
    analysis = elixir.OneToOne('Analysis', cascade='all')
    report = elixir.OneToOne('Report', cascade='all')
    extraData = elixir.OneToOne('ExtraData')
    staticMossGraphs = elixir.OneToMany('StaticMossGraph')
    staticJPlagGraphs = elixir.OneToMany('StaticJPlagGraph')
    #using_table_options(UniqueConstraint('course_id', 'name'))

    def __repr__(self):
        return "<assignment: %s in %s>" % (self.name, self.course.name)
    
class FileSet(elixir.Entity):
    name = elixir.Field(elixir.String(1024))
    submissions = elixir.OneToMany('Submission', cascade='all')
    assignments = elixir.ManyToMany('Assignment')
    offering = elixir.ManyToOne('Offering')
    course = elixir.ManyToOne('Course') #why?
    isSolutionSet = elixir.Field(elixir.Boolean())
    tempDir = elixir.Field(elixir.String(1024))
    subdir = elixir.Field(elixir.String(1024))
    timestamp = elixir.Field(elixir.DateTime(), default=datetime.datetime.today())
    isComplete = elixir.Field(elixir.Boolean())
    extraData = elixir.OneToOne('ExtraData')
    
    def __cmp__(self, other):
        if isinstance(other, FileSet) or isinstance(other, SolutionFileSet) or isinstance(other, BaseFileSet):
            return cmp(self.name, other.name)
        else:
            return cmp(self.__hash__(), other.__hash__())
        
class BaseFileSet(FileSet):
    elixir.using_options(inheritance='multi')

class SolutionFileSet(FileSet):
    elixir.using_options(inheritance='multi')
    
class Submission(elixir.Entity):
    submissionFiles = elixir.OneToMany('SubmissionFile', cascade='all')
    fileset = elixir.ManyToOne('FileSet')
    #analysisPseudonyms = elixir.ManyToOne('AnalysisPseudonym')
    extraData = elixir.OneToOne('ExtraData')
    analysisPseudonyms = elixir.OneToMany('AnalysisPseudonym')

class StudentSubmission(Submission):
    elixir.using_options(inheritance='multi')

    # each student can have multiple submissions per (offering, assignment) --
    # e.g. early, regular, late handin
    offering = elixir.ManyToOne('Offering')
    student = elixir.ManyToOne('Student')
    partners = elixir.ManyToMany('Student')
    partnerLinks = elixir.ManyToMany('Submission')

    def __repr__(self):
        return "<student submission: %s %s %d by %s>" %       (self.offering.course.name,
                                                               self.offering.semester.season,
                                                               self.offering.semester.year,
                                                               self.student.netid)

class SolutionSubmission(Submission):
    elixir.using_options(inheritance='multi')
    
    def __repr__(self):
        return "<solution submission: %s>" % self.fileset.name
    
class BaseSubmission(Submission):
    elixir.using_options(inheritance='multi')
    
    def __repr__(self):
        return "<base submission: %s>" % self.fileset.name

class PartnerLink(elixir.Entity):
    submission1 = elixir.ManyToMany('Submission')
    submission2 = elixir.ManyToMany('Submission')
    type = elixir.Field(Enum(["direct", "indirect"], strict=True))
    linkage = elixir.ManyToMany('Submission')
    extraData = elixir.OneToOne('ExtraData')
    images = elixir.ManyToMany('Image')

class SubmissionFile(elixir.Entity):
    #submission = elixir.ManyToOne('Submission', primary_key=True)
    #name = elixir.Field(elixir.String(40), primary_key=True)
    submission = elixir.ManyToOne('Submission')
    name = elixir.Field(elixir.String(1024))
    content = elixir.Field(MSLongText())
    meta = elixir.Field(elixir.Boolean())
    extraData = elixir.OneToOne('ExtraData')
    #using_table_options(UniqueConstraint('submission_id', 'name'))

    def __repr__(self):
        return "<file: %s for %s>" % (self.name, self.submission)

class Student(elixir.Entity):
    # technically, NetIDs can be changed or recycled,
    # so we really should be using the student UIN
    netid = elixir.Field(elixir.String(10), unique=True)
    submissions = elixir.OneToMany('StudentSubmission', cascade='all')
    levelName = elixir.Field(elixir.String(128))
    programName = elixir.Field(elixir.String(128))
    givenName = elixir.Field(elixir.String(128))
    displayName = elixir.Field(elixir.String(128))
    surName = elixir.Field(elixir.String(128))
    leftUIUC = elixir.Field(elixir.String(32))
    dn = elixir.Field(elixir.String(1024))
    extraData = elixir.OneToOne('ExtraData')
    offerings = elixir.ManyToMany('Offering')
    def __repr__(self):
        return "<student: netid: %s name: %s >" % (self.netid, self.displayName)
    
    def __cmp__(self, other):
        if isinstance(other, Student):
            return cmp(self.netid, other.netid)
        else:
            return cmp(self.__hash__(), other.__hash__())

class Analysis(elixir.Entity):
    assignment = elixir.ManyToOne('Assignment')
    mossAnalysis = elixir.OneToOne('MossAnalysis', inverse='analysis', cascade='all')
    jPlagAnalysis = elixir.OneToOne('JPlagAnalysis', inverse='analysis', cascade='all')
    analysisPseudonyms = elixir.OneToMany('AnalysisPseudonym', cascade='all')
    workDirectory = elixir.Field(elixir.String(255))
    webDirectory = elixir.Field(elixir.String(255))
    complete = elixir.Field(elixir.Boolean(), default=False)
    timestamp = elixir.Field(elixir.DateTime(), default=datetime.datetime.today())
    extraData = elixir.OneToOne('ExtraData')
    
    def __repr__(self):
        return "<analysis: %s>" % self.assignment
    
    def __cmp__(self, other):
        if isinstance(other, Analysis):
            return cmp(self.timestamp, other.timestamp)
        else:
            return cmp(self.__hash__(), other.__hash__())

class Report(elixir.Entity):
    assignment = elixir.ManyToOne('Assignment')
    mossReport = elixir.OneToOne('MossReport', inverse='report', cascade='all')
    jPlagReport = elixir.OneToOne('JPlagReport', inverse='report', cascade='all')
    complete = elixir.Field(elixir.Boolean(), default=False)
    extraData = elixir.OneToOne('ExtraData')
    
    def __repr__(self):
        return "<report: %s>" % self.assignment

class EngineReport(elixir.Entity):
    complete = elixir.Field(elixir.Boolean(), default=False)

class MossReport(EngineReport):
    elixir.using_options(inheritance='multi')
    mossReportFiles = elixir.OneToMany('MossReportFile', cascade='all')
    extraData = elixir.OneToOne('ExtraData')
    report = elixir.ManyToOne('Report')
    complete = elixir.Field(elixir.Boolean(), default=False)
    
    def __repr__(self):
        return "<moss report: %s>" % self.report
    
    def __cmp__(self, other):
        if isinstance(other, MossReport):
            return cmp(self.id, other.id)
        else:
            return cmp(self.__hash__(), other.__hash__())
    

class MossReportFile(elixir.Entity):
    mossReport = elixir.ManyToOne('MossReport')
    name = elixir.Field(elixir.String(512))
    content = elixir.Field(MSLongText())
    extraData = elixir.OneToOne('ExtraData')
    using_table_options(UniqueConstraint('mossReport_enginereport_id', 'name'))

    def __repr__(self):
        return "<moss report file: %s for %s>" % (self.name, self.mossReport)                

class JPlagReport(EngineReport):
    elixir.using_options(inheritance='multi')
    report = elixir.ManyToOne('Report')
    complete = elixir.Field(elixir.Boolean(), default=False)
    
    jPlagReportFiles = elixir.OneToMany('JPlagReportFile', cascade='all')
    extraData = elixir.OneToOne('ExtraData')
    def __repr__(self):
        return "<jplag report: %s>" % self.report
    
class JPlagReportFile(elixir.Entity):
    #mossReport = elixir.ManyToOne('MossReport', primary_key=True)
    #name = elixir.Field(elixir.String(40), primary_key=True)
    jPlagReport = elixir.ManyToOne('JPlagReport')
    name = elixir.Field(elixir.String(512))
    content = elixir.Field(MSLongText())
    extraData = elixir.OneToOne('ExtraData')
    using_table_options(UniqueConstraint('jPlagReport_enginereport_id', 'name'))

    def __repr__(self):
        return "<jplag report file: %s for %s>" % (self.name, self.mossReport)  

class AnalysisPseudonym(elixir.Entity):
    analysis = elixir.ManyToOne('Analysis', constraint_kwargs={"name": "ap_a_fk"})
    pseudonym = elixir.Field(elixir.String(512))
    #XXX elixir.using_table_options(sqlalchemy.UniqueConstraint('analysisExecution', 'submission'))
    extraData = elixir.OneToOne('ExtraData')
    submission = elixir.ManyToOne('Submission')
    using_table_options(UniqueConstraint('analysis_id', 'pseudonym', name='aid_psid_fk'))


    def __repr__(self):
        return "<analysis pseudonym: %s to %s in %s>" % (self.submission, self.pseudonym, self.analysis)

class EngineAnalysis(elixir.Entity):
    workDirectory = elixir.Field(elixir.String(255))
    complete = elixir.Field(elixir.Boolean(), default=False)
    extraData = elixir.OneToOne('ExtraData')


class MossMatch(elixir.Entity):
    mossAnalysis = elixir.ManyToOne('MossAnalysis')
    submission1 = elixir.ManyToOne('Submission')
    submission2 = elixir.ManyToOne('Submission')
    score1 = elixir.Field(elixir.Integer())
    score2 = elixir.Field(elixir.Integer())
    link = elixir.Field(elixir.String(255))
    extraData = elixir.OneToOne('ExtraData')
    hidden = elixir.Field(elixir.Boolean(), default=False)
        
    def get_score(self):
        if self.score1 > self.score2:
            return self.score1
        else:
            return self.score2
        
    def __cmp__(self, other):
        if isinstance(other, MossMatch):
            return cmp(self.get_score(), other.get_score())
        else:
            return cmp(self.__hash__(), other.__hash__())

    def __repr__(self):
        return "<moss match: %s with %d to %s with %d>" % (self.submission1, self.score1,
                                                           self.submission2, self.score2)
class MossAnalysis(EngineAnalysis):
    elixir.using_options(inheritance='multi')
    analysis = elixir.ManyToOne('Analysis')
    matches = elixir.OneToMany('MossMatch', cascade='all')
    pruned = elixir.Field(elixir.Boolean(), default=False)
    prunedOffering = elixir.ManyToOne('Offering')
    images = elixir.ManyToMany('Image')
    #pruned_offering_id = elixir.Field(elixir.Integer()) #hack since sqlalchemy-migrate doesnt seem to allow me to create relations
    #hack...see note above
    #def get_pruned_offering(self):
#        return Offering.query.filter_by(id=self.pruned_offering_id).first()
#    
#    def set_pruned_offering(self, offering):
#        self.pruned_offering_id = offering.id
#        Session.commit()

    def __repr__(self):
        return "<moss analysis: %s>" % self.analysis
    
class JPlagAnalysis(EngineAnalysis):
    elixir.using_options(inheritance='multi')
    analysis = elixir.ManyToOne('Analysis')
    matches = elixir.OneToMany('JPlagMatch')
    pruned = elixir.Field(elixir.Boolean(), default=False)
    prunedOffering = elixir.ManyToOne('Offering')
    suffixes = elixir.Field(elixir.String(1024), default="")
    minMatchLength = elixir.Field(elixir.Integer())
    basecodeDirectory = elixir.Field(elixir.String(1024), default="none")
    clusterType = elixir.Field(Enum(['none', 'min', 'avr', 'max'], strict=True), default='none')
    images = elixir.ManyToMany('Image')
    
    
    def __repr__(self):
        return "<jplag analysis: %s>" % self.analysis

class JPlagMatch(elixir.Entity):
    jPlagAnalysis = elixir.ManyToOne('JPlagAnalysis')
    submission1 = elixir.ManyToOne('Submission')
    submission2 = elixir.ManyToOne('Submission')
    score1 = elixir.Field(elixir.Integer())
    score2 = elixir.Field(elixir.Integer())
    link = elixir.Field(elixir.String(255))
    extraData = elixir.OneToOne('ExtraData')
    
    def get_score(self):
        if self.score1 > self.score2:
            return self.score1
        else:
            return self.score2
        
    def __cmp__(self, other):
        if isinstance(other, JPlagMatch):
            return cmp(self.get_score(), other.get_score())
        else:
            return cmp(self.__hash__(), other.__hash__())

    def __repr__(self):
        return "<jplag match: %s with %d to %s with %d>" % (self.submission1, self.score1,
                                                           self.submission2, self.score2)
    
class StaticMossGraph(elixir.Entity):
    assignment = elixir.ManyToOne('Assignment')
    requestingUser= elixir.ManyToOne('User')
    threshold= elixir.Field(elixir.Integer())
    includeSolution= elixir.Field(elixir.Boolean())
    anonymize=elixir.Field(elixir.Boolean())
    singletons=elixir.Field(elixir.Boolean())
    layoutEngine = elixir.Field(elixir.String(32))
    imageData = elixir.Field(MSMediumBlob())
    mediumData = elixir.Field(MSMediumBlob())
    thumbnailData = elixir.Field(MSMediumBlob())
    isComplete = elixir.Field(elixir.Boolean())
    extraData = elixir.OneToOne('ExtraData')
    
    def to_str(self):
        return "Graph: Threshold=%i, Solution Included=%s, Anonymous=%s, Singletons Included=%s, Layout Engine Used=%s"%(self.threshold, self.includeSolution, self.anonymize,self.singletons,self.layoutEngine)

class StaticJPlagGraph(elixir.Entity):
    assignment = elixir.ManyToOne('Assignment')
    requestingUser= elixir.ManyToOne('User')
    threshold= elixir.Field(elixir.Integer())
    includeSolution= elixir.Field(elixir.Boolean())
    anonymize=elixir.Field(elixir.Boolean())
    singletons=elixir.Field(elixir.Boolean())
    layoutEngine = elixir.Field(elixir.String(32))
    imageData = elixir.Field(MSMediumBlob())
    mediumData = elixir.Field(MSMediumBlob())
    thumbnailData = elixir.Field(MSMediumBlob())
    isComplete = elixir.Field(elixir.Boolean())
    extraData = elixir.OneToOne('ExtraData')
    
    def to_str(self):
        return "Graph: Threshold=%i, Solution Included=%s, Anonymous=%s, Singletons Included=%s, Layout Engine Used=%s"%(self.threshold, self.includeSolution, self.anonymize,self.singletons,self.layoutEngine)
    
class Image(elixir.Entity):
    name = elixir.Field(elixir.String(1024))
    title = elixir.Field(elixir.String(1024))
    type = elixir.Field(elixir.String(1024))
    filename = elixir.Field(elixir.String(1024))
    owner_type = elixir.Field(elixir.String(128))
    owner_id = elixir.Field(elixir.Integer())
    imageData = elixir.Field(MSMediumBlob())
    mediumData = elixir.Field(MSMediumBlob())
    thumbnailData = elixir.Field(MSMediumBlob())
    extraData = elixir.OneToOne('ExtraData')
    
class ExtraData(elixir.Entity):
    data = elixir.Field(elixir.PickleType(), default={}) 
    
    #necessary crap
    user = elixir.ManyToOne('User')
    semester = elixir.ManyToOne('Semester')
    course = elixir.ManyToOne('Course')
    offering = elixir.ManyToOne('Offering')
    assignment = elixir.ManyToOne('Assignment')
    fileset = elixir.ManyToOne('FileSet')
    submission = elixir.ManyToOne('Submission')
    submissionFile = elixir.ManyToOne('SubmissionFile')
    student = elixir.ManyToOne('Student')
    analysis = elixir.ManyToOne('Analysis')
    report = elixir.ManyToOne('Report')
    mossReport = elixir.ManyToOne('MossReport')
    mossReportFile = elixir.ManyToOne('MossReportFile')
    jPlagReport = elixir.ManyToOne('JPlagReport')
    jPlagReportFile = elixir.ManyToOne('JPlagReportFile')
    analysisPseudonym = elixir.ManyToOne('AnalysisPseudonym')
    engineAnalysis = elixir.ManyToOne('EngineAnalysis')
    mossMatch = elixir.ManyToOne('MossMatch')
    jPlagMatch = elixir.ManyToOne('JPlagMatch')
    staticMossGraph = elixir.ManyToOne('StaticMossGraph')
    staticJPlagGraph = elixir.ManyToOne('StaticJPlagGraph')
    image = elixir.ManyToOne('Image')
    partnerLink = elixir.ManyToOne('PartnerLink')