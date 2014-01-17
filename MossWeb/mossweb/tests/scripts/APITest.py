from paste.deploy import loadapp
from paste.script.appinstall import SetupCommand
from pylons import config, url
from routes.util import URLGenerator
from webtest import TestApp

import pylons.test
from elixir import *
from mossweb.model import *
from mossweb.model import meta
from mossweb.model.model import *
from mossweb import model as model
from sqlalchemy import engine_from_config
from mossweb.controllers.api import ApiController

__all__ = ['environ', 'url', 'TestController', 'TestModel']


# Invoke websetup with the current config file
# SetupCommand('setup-app').run([config['__file__']])

# additional imports ...
import os
from paste.deploy import appconfig
from mossweb.config.environment import load_environment

test_file = os.path.join('/home/chuck/Aptana Studio Workspace/mossweb/MossWeb/development_cemeyer2_local_mysql.ini')
conf = appconfig('config:' + test_file)
load_environment(conf.global_conf, conf.local_conf)
environ = {}

engine = engine_from_config(config, 'sqlalchemy.')
model.init_model(engine)
metadata = elixir.metadata
Session = elixir.session = meta.Session
metadata.bind.echo = False
import xmlrpclib
srvr = xmlrpclib.Server("http://localhost:5000/api")

def test_getAnalysis():
    for id in Session.query(Analysis.id):
        try:
            srvr.getAnalysis(int(id[0]))
        except:
            print "getAnalysis: error on params: id: "+str(id[0])

def test_getAnalysisPseudonym():
    for id in Session.query(AnalysisPseudonym.id):
        try:
            srvr.getAnalysis(int(id[0]))
        except:
            print "getAnalysisPseudonym: error on params: id: "+str(id[0])

def test_getAssignment():
    for id in Session.query(Analysis.id):
        try:
            srvr.getAnalysis(int(id[0]))
        except:
            print "getAssignment: error on params: id: "+str(id[0])

def test_getAssignments():
    for id in Session.query(Course.id):
        try:
            srvr.getAssignments(int(id[0]))
        except:
            print "getAssignments: error on params: id: "+str(id[0])

def test_getCourse():
    for id in Session.query(Course.id):
        try:
            srvr.getAnalysis(int(id[0]))
        except:
            print "getCourse: error on params: id: "+str(id[0])

def test_getCourses():
    try:
        srvr.getCourses()
    except:
        print "getCourses: error"

def test_getFileSet():
    for id in Session.query(FileSet.id):
        try:
            srvr.getFileSet(int(id[0]))
        except:
            print "getFileSet: error on params: id: "+str(id[0])

def test_getMossAnalysis():
    for id in Session.query(MossAnalysis.id):
        try:
            srvr.getMossAnalysis(int(id[0]))
        except:
            print "getMossAnalysis: error on params: id: "+str(id[0])

def test_getMossMatch():
    for id in Session.query(MossMatch.id):
        try:
            srvr.getMossMatch(int(id[0]))
        except Exception, e:
            print "getMossMatch: error on params: id: "+str(id[0])
            print str(e)

def test_getMossReport():
    for id in Session.query(MossReport.id):
        try:
            srvr.getMossReport(int(id[0]))
        except:
            print "getMossReport: error on params: id: "+str(id[0])

def test_getOffering():
    for id in Session.query(Offering.id):
        try:
            srvr.getOffering(int(id[0]))
        except Exception, e:
            print "getOffering: error on params: id: "+str(id[0])
            print str(e)

def test_getReport():
    for id in Session.query(Report.id):
        try:
            srvr.getReport(int(id[0]))
        except Exception, e:
            print "getReport: error on params: id: "+str(id[0])
            print str(e)

def test_getSemester():
    for id in Session.query(Semester.id):
        try:
            srvr.getSemester(int(id[0]))
        except Exception, e:
            print "getSemester: error on params: id: "+str(id[0])
            print str(e)

def test_getStudent():
    for id in Session.query(Student.id):
        try:
            import random
            random.seed()
            rand = random.randrange(1,101)
            srvr.getStudent(int(id[0]))
            srvr.getStudent(int(id[0]), True)
            srvr.getStudent(int(id[0]), True, rand)
        except Exception, e:
            print "getStudent: error on params: id: "+str(id[0])
            print str(e)

def test_getStudentByNetid():
    for id in Session.query(Student.netid):
        try:
            import random
            random.seed()
            rand = random.randrange(1,101)
            srvr.getStudent(int(id[0]))
            srvr.getStudent(int(id[0]), True)
            srvr.getStudent(int(id[0]), True, rand)
        except Exception, e:
            print "getStudentByNetid: error on params: id: "+str(id[0])
            print str(e)

def test_getSubmission():
    for id in Session.query(Submission.id):
        try:
            srvr.getSubmission(int(id[0]))
        except Exception, e:
            print "getSubmission: error on params: id: "+str(id[0])
            print str(e)

def test_getSubmissionFile():
    for id in Session.query(SubmissionFile.id):
        try:
            srvr.getSubmissionFile(int(id[0]))
            srvr.getSubmissionFile(int(id[0]), True)
        except Exception, e:
            print "getSubmissionFile: error on params: id: "+str(id[0])
            print str(e)

print "getAnalysis"
test_getAnalysis()
print "getAnalysisPseudonym"
test_getAnalysisPseudonym()
print "getAssignment"
test_getAssignment()
print "getAssignments"
test_getAssignments()
print "getCourse"
test_getCourse()
print "getCourses"
test_getCourses()
print "getFileSet"
test_getFileSet()
print "getMossAnalysis"
test_getMossAnalysis()
print "getMossMatch"
test_getMossMatch()
print "getMossReport"
test_getMossReport()
print "getOffering"
test_getOffering()
print "getReport"
test_getReport()
print "getSemester"
test_getSemester()
print "getStudent"
test_getStudent()
print "getStudentByNetid"
test_getStudentByNetid()
print "getSubmission"
test_getSubmission()
print "getSubmissionFile"
test_getSubmissionFile()


print "DONE"

