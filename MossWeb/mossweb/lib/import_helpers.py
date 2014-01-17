'''
Created on Mar 29, 2010

@author: chuck
'''

from mossweb.model.model import *
from mossweb.model import Session
import os
import logging
import re
from mossweb.lib import ldap_helpers as lh

log = logging.getLogger(__name__)

def import_files(fileset, files, meta_file_name):
    if isinstance(fileset, SolutionFileSet) or isinstance(fileset, BaseFileSet):
        __import_special(fileset, files)    
    else:
        __import_student_submissions(fileset, files, meta_file_name)
    return fileset

def __import_special(fileset, files):
    directoryPath = fileset.tempDir
    subdir = fileset.subdir
    offering = fileset.offering
    sub = None
    if isinstance(fileset, SolutionFileSet):
        sub = SolutionSubmission()
    elif isinstance(fileset, BaseFileSet):
        sub = BaseSubmission()
    
    regex = re.compile("^("+directoryPath+")("+os.sep+")("+subdir+")("+os.sep+")(.*)")
    if len(subdir) == 0:
        regex = re.compile("^("+directoryPath+")("+os.sep+")(.*)")
    
    for filename in files:
        match = regex.match(filename)
        if match is None:
            continue
        shortname = "_".join(match.group(3).split(os.sep))
        if len(subdir) > 0:
            shortname = "_".join(match.group(5).split(os.sep))
        log.debug("filename: "+filename)
        log.debug("shortname: "+shortname)
        
        content = __tryread(filename)
        if not content == None:
            sub.submissionFiles.append(SubmissionFile(name=shortname, content=content, meta=False))
            
    fileset.submissions.append(sub)
    fileset.isComplete = True

def __import_student_submissions(fileset, files, meta_file_name):
    directoryPath = fileset.tempDir
    subdir = fileset.subdir
    offering = fileset.offering
    submissions = {}
    length = len(directoryPath)
    #need to modify this regex to be much better
    #regex = re.compile("^("+directoryPath+")("+os.sep+")(.*)("+os.sep+")("+subdir+")("+os.sep+")(.*)")
    students_to_update = []
    for filename in files:
        chopped = filename[length+1:].split(os.sep)
        netid = unicode(chopped[0])
        #subdir = chopped[1]
        shortname = unicode("_".join(chopped[2:]))
        #match = regex.match(filename)
        #if match is None:
        #    continue
        #netid = match.group(3)
        #shortname = match.group(7)
        log.debug("filename: "+filename)
        log.debug("netid: "+netid)
        log.debug("shortname: "+shortname)
        
        student = None
        for s in Student.query.filter_by(netid=netid):
            student = s
        if student is None:
            #log.debug("creating student with netid: "+netid)
            student = Student(netid=netid)
            student.offerings.append(fileset.offering)
            #lh.populate_student_from_active_directory(student)
        if student not in students_to_update:
            students_to_update.append(student)
        if netid in submissions:
            sub = submissions[netid]
        else:
            sub = StudentSubmission(student=student, offering=offering)
            submissions[netid] = sub
        content = __tryread(filename)
        if not content == None:
            sub.submissionFiles.append(SubmissionFile(name=shortname, content=content, meta=filename.endswith(meta_file_name)))
    #log.debug(str(submissions))
    for netid in submissions:
        fileset.submissions.append(submissions[netid])
    fileset.isComplete = True
    #update all the students in one paged ldap query rather than hundreds of individual ones
    lh.populate_student_from_active_directory(students_to_update)


def __tryread(filename):
    try:
        f = open(filename, 'r')
        content = f.read()
        f.close()
        return content.encode('ascii', 'xmlcharrefreplace')
    except:
        return None