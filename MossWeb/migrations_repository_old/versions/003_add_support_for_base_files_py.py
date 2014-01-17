from sqlalchemy import *
from migrate import *
from elixir import *
from mossweb.model import model, Session
from sqlalchemy.exc import OperationalError

meta = MetaData()

def safe_create_table(model):
    try:
        model.table.create()
    except OperationalError, e:
        "ERROR CREATING TABLE---"+str(e)

def safe_create_row_type(model, engine, default):
    try:
        col = model.table.columns.get("row_type")
        col.create(model.table, populate_default=False)
        sql = "UPDATE "+model.table.name+" SET row_type='"+default+"' WHERE row_type is NULL;"
        engine.execute(sql)
    except OperationalError, e:
        print "ERROR CREATING row_type---"+str(e)
    
def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.bind.echo = True
    setup_all()
    safe_create_table(model.SolutionSemester)
    safe_create_table(model.BaseSemester)
    safe_create_table(model.BaseFileSet)
    safe_create_table(model.SolutionFileSet)
    safe_create_table(model.BaseSubmission)
    
    safe_create_row_type(model.Semester, migrate_engine, "semester")
    safe_create_row_type(model.FileSet, migrate_engine, "fileset")
    
    year = -1
    #convert soln semesters
    for semester in model.Semester.query.filter(model.Semester.isSolution==True).all():
        s = model.SolutionSemester(year=year, season=u"Fall", isSolution=True)
        changed_offerings = model.Offering.query.filter_by(semester=semester).all()
        for offering in changed_offerings:
            offering.semester = s
        year = year - 1
        Session.delete(semester)
        Session.commit()
    s = model.BaseSemester(year=year, season=u"Fall", isSolution=True)
    Session.commit()
    #convert soln filesets
    for fileset in model.FileSet.query.filter(model.FileSet.isSolutionSet==True).all():
        f = model.SolutionFileSet()
        f.name = fileset.name
        f.submissions = fileset.submissions
        f.assignments = fileset.assignments
        f.offering = fileset.offering
        f.course = fileset.course
        f.isSolutionSet = fileset.isSolutionSet
        f.tempDir = fileset.tempDir
        f.subdir = fileset.subdir
        f.timestamp = fileset.timestamp
        f.isComplete = fileset.isComplete
        fileset.submissions = []
        fileset.assignments = []
        fileset.offering = None
        fileset.course = None
        changed_courses = model.Course.query.filter(model.Course.filesets.contains(fileset)).all()
        for course in changed_courses:
            course.filesets.remove(fileset)
            course.filesets.append(f)
        changed_offerings = model.Offering.query.filter(model.Offering.filesets.contains(fileset)).all()
        for offering in changed_offerings:
            offering.filesets.remove(fileset)
            offering.filesets.append(f)
        changed_assignments = model.Assignment.query.filter(model.Assignment.filesets.contains(fileset)).all()
        for assignment in changed_assignments:
            assignment.filesets.remove(fileset)
            assignment.filesets.append(f)
        changed_submissions = model.Submission.query.filter_by(fileset=fileset).all()
        for sub in changed_submissions:
            sub.semester = s
        Session.delete(fileset)
        Session.commit()

def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    setup_all()
    