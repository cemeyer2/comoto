'''
Created on Mar 31, 2010

@author: chuck
'''

from mossweb.model.model import *
import logging
from pylons import config, session
from pylons.controllers.util import abort


log = logging.getLogger(__name__)

import os, tempfile, random, shutil, subprocess, re

import BeautifulSoup

def __rand_string(length):
    alphabet = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    str = ''
    return str.join(random.sample(alphabet,length))

def create_random_public_directory():
    rand_dir = __rand_string(32)
    public_dir = config['pylons.paths']['static_files']
    moss_dir = 'moss_analysis'
    output_path = os.path.join(public_dir, moss_dir, rand_dir)
    #os.makedirs(output_path)
    return output_path

def do_moss_deep_solution(assignment, student_fileset, solution_filesets, base_filesets=[]):
    session['analysis_status'] = "Running deep solution analysis"
    session.save()
    session.persist()
    analysis = assignment.analysis
    total = float(len(student_fileset.submissions))
    left = float(len(student_fileset.submissions))
    for submission in student_fileset.submissions: 
        #do moss
        def preprocess_submission(sub, work_dir):
            pseudo = AnalysisPseudonym.query.filter_by(submission=sub).filter_by(analysis=analysis).first()
            allfiles = []
            subdir = os.path.join(work_dir, pseudo.pseudonym)
            try:
                os.makedirs(subdir)
            except:
                pass
            for subfile in filter(lambda x: not x.meta, sub.submissionFiles):
                #next 7 lines handle files that reside in subfolders
                name = subfile.name.replace(os.sep, "-")
                filename = os.path.join(subdir, name)
                f = open(filename, 'w')
                if(isinstance(subfile.content, unicode)):
                    f.write(subfile.content.encode('ascii', 'xmlcharrefreplace'))
                else:
                    f.write(subfile.content)
                f.close()
                allfiles.append(os.path.join(pseudo.pseudonym, name))
            return allfiles
        def preprocess_basesubmission(sub, work_dir):
            allfiles = []
            subdir = os.path.join(work_dir, 'base')
            try:
                os.makedirs(subdir)
            except:
                pass
            for subfile in filter(lambda x: not x.meta, sub.submissionFiles):
                #next 7 lines handle files that reside in subfolders
                name = subfile.name.replace(os.sep, "-")
                filename = os.path.join(subdir, name)
                f = open(filename, 'w')
                if(isinstance(subfile.content, unicode)):
                    f.write(subfile.content.encode('ascii', 'xmlcharrefreplace'))
                else:
                    f.write(subfile.content)
                f.close()
                allfiles.append(os.path.join('base', name))
            return allfiles         
        #preprocess the files
        work_dir = tempfile.mkdtemp()
        allfiles = []
        allfiles.extend(preprocess_submission(submission, work_dir))
        for sfs in solution_filesets:
            for solsub in sfs.submissions:
                allfiles.extend(preprocess_submission(solsub, work_dir))
        base_work_dir = tempfile.mkdtemp()
        basefiles = []
        for bfs in base_filesets:
            for basesub in bfs.submissions:
                basefiles.extend(preprocess_basesubmission(basesub, base_work_dir))
        moss_dir = tempfile.mkdtemp()
        moss_analysis = MossAnalysis.query.filter_by(analysis=analysis).first()
        moss_path = config["app_conf"]["moss_path"]
        moss_args = [moss_path, '-m', str(50), '-n', str(100), '-l', str(assignment.language), '-o', str(moss_dir), '-d']
        for base_file in basefiles:
            moss_args.append('-b')
            moss_args.append(os.path.join(base_work_dir,base_file))
        moss_args.extend(allfiles)
        log.debug("MOSS CMD="+str(moss_args))
        moss_process = subprocess.Popen(moss_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=work_dir)
        while True:
            output = moss_process.stdout.readline().strip()
            log.debug(output)
            if output == '' and moss_process.poll() != None:
                break
        moss_report = assignment.report.mossReport
        for sourceFile in os.listdir(moss_dir):
            f = open(os.path.join(moss_dir, sourceFile), 'r')
            content = unicode(f.read())
            f.close()
            moss_report.mossReportFiles.append(MossReportFile(name=sourceFile+"-"+submission.student.netid+"-sol-compare", content=content))
        #end running moss
        #start calculating results
        results_stream = open(os.path.join(moss_dir, 'index.html'))
        soup = BeautifulSoup.BeautifulSoup(results_stream.read())
        results_stream.close()
        for row in soup.find('table').findAll('tr'):
            if row.find('th'):
                continue
            studentData = row.findAll('a', limit=2)
            text1 = studentData[0].contents[0]
            text2 = studentData[1].contents[0]
            link = studentData[0]['href']
    
            textExp = re.compile(r'(\S+)/ \((\d+)%\)')
#            log.debug("text1="+text1)
            (pseudonym1, score1) = textExp.match(text1).group(1, 2)
#            log.debug("text2="+text2)
            (pseudonym2, score2) = textExp.match(text2).group(1, 2)
            
            submission1 = AnalysisPseudonym.query.filter_by(analysis=assignment.analysis).filter_by(pseudonym=pseudonym1).first().submission
            submission2 = AnalysisPseudonym.query.filter_by(analysis=assignment.analysis).filter_by(pseudonym=pseudonym2).first().submission
            netid = ""
            if submission1.row_type == 'studentsubmission':
                netid = submission1.student.netid
            elif submission2.row_type == 'studentsubmission':
                netid = submission2.student.netid
            else:
                continue
            match = MossMatch(submission1=submission1, score1=int(score1),
                      submission2=submission2, score2=int(score2),
                      link=link+"-"+netid+"-sol-compare",
                      mossAnalysis=moss_analysis)
        #end calculating results
        #start cleanup
        shutil.rmtree(work_dir)
        shutil.rmtree(base_work_dir)
        shutil.rmtree(moss_dir)
        #end cleanup
        left = left - 1
        pct = 100 * ((total-left)/total)
        pct = round(pct, 2)
        log.debug("total: "+str(total))
        log.debug("left: "+str(left))
        log.debug("pct: "+str(pct))
        session['analysis_status'] = "Deep solution analysis: "+str(pct)+"% complete"
        session.save()
        session.persist()

def do_moss(assignment, moss_repeat_count, moss_max_matches):
    session['analysis_status'] = "Preprocessing files for analysis"
    session.save()
    session.persist()
    analysis = Analysis(assignment=assignment, workDirectory=tempfile.mkdtemp(), webDirectory=create_random_public_directory())
    allfiles = []
    submission_count = 0
    non_base_filesets = filter(lambda fileset: not isinstance(fileset,BaseFileSet), assignment.filesets)
    base_filesets = filter(lambda fileset: isinstance(fileset,BaseFileSet), assignment.filesets)
    for fileset in non_base_filesets:
        submission_count = submission_count + len(fileset.submissions)
    nums = range(0, submission_count)
    random.shuffle(nums)
    for fileset in non_base_filesets:
        for sub in fileset.submissions:
            pseudo = AnalysisPseudonym(analysis=analysis, submission=sub, pseudonym=submission_to_str(sub)+"_"+assignment.name.replace(" ","_"))
            subdir = os.path.join(analysis.workDirectory, pseudo.pseudonym)
            try:
                os.makedirs(subdir)
            except:
                pass
            for subfile in filter(lambda x: not x.meta, sub.submissionFiles):
                #next 7 lines handle files that reside in subfolders
                name = subfile.name.replace(os.sep, "-")
                filename = os.path.join(subdir, name)
                f = open(filename, 'w')
                if(isinstance(subfile.content, unicode)):
                    f.write(subfile.content.encode('ascii', 'xmlcharrefreplace'))
                else:
                    f.write(subfile.content)
                f.close()
                allfiles.append(os.path.join(pseudo.pseudonym, name))
    base_args = []
    base_tempdirs = []
    for fileset in base_filesets:
        tempdir = tempfile.mkdtemp()
        base_tempdirs.append(tempdir)
        for sub in fileset.submissions:
            subdir = os.path.join(tempdir, __rand_string(10))
            try:
                os.makedirs(subdir)
            except:
                pass
            for subfile in sub.submissionFiles:
                name = subfile.name.replace(os.sep, "-")
                filename = os.path.join(subdir, name)
                f = open(filename, 'w')
                if(isinstance(subfile.content, unicode)):
                    f.write(subfile.content.encode('ascii', 'xmlcharrefreplace'))
                else:
                    f.write(subfile.content)
                f.close()
                base_args.append('-b')
                base_args.append(filename)
    session['analysis_status'] = "Running Moss analysis engine"
    session.save()
    session.persist()
    moss_analysis = MossAnalysis(analysis=analysis, workDirectory=tempfile.mkdtemp())
    moss_path = config["app_conf"]["moss_path"]
    moss_args = [moss_path, '-m', str(moss_repeat_count), '-n', str(moss_max_matches), '-l', str(assignment.language), '-o', str(moss_analysis.workDirectory), '-d']
    moss_args.extend(base_args)
    moss_args.extend(allfiles)
    log.debug("MOSS CMD="+str(moss_args))
    moss_process = subprocess.Popen(moss_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=analysis.workDirectory)
    while True:
        output = moss_process.stdout.readline().strip()
        #log.debug(output)
        if output == '' and moss_process.poll() != None:
            break
    analysis.complete = True
    moss_analysis.complete = True
    session['analysis_status'] = "Importing analysis results"
    session.save()
    session.persist()
    report = assignment.report = Report(assignment=assignment, mossReport=MossReport())
    moss_report = report.mossReport
    
    for sourceFile in os.listdir(moss_analysis.workDirectory):
        f = open(os.path.join(moss_analysis.workDirectory, sourceFile), 'r')
        content = unicode(f.read())
        f.close()
        moss_report.mossReportFiles.append(MossReportFile(name=sourceFile, content=content))
        
    moss_report.complete = True
    
    for tempdir in base_tempdirs:
        shutil.rmtree(tempdir) #clean up after ourselves
    
    return analysis

def calculate_moss_matches(assignment):
    
    session['analysis_status'] = "Computing analysis results"
    session.save()
    session.persist()
    analysis = assignment.analysis
    moss_analysis = analysis.mossAnalysis

    results_stream = open(os.path.join(moss_analysis.workDirectory, 'index.html'))
    soup = BeautifulSoup.BeautifulSoup(results_stream.read())
    results_stream.close()

    for row in soup.find('table').findAll('tr'):
        if row.find('th'):
            continue

        studentData = row.findAll('a', limit=2)
        text1 = studentData[0].contents[0]
        text2 = studentData[1].contents[0]
        link = studentData[0]['href']

        # 0/ (12%)
        textExp = re.compile(r'(\S+)/ \((\d+)%\)')
        log.debug("text1="+text1)
        (pseudonym1, score1) = textExp.match(text1).group(1, 2)
        log.debug("text2="+text2)
        (pseudonym2, score2) = textExp.match(text2).group(1, 2)

        #submission1 = AnalysisPseudonym.get((assignment.analysis.id, pseudonym1)).submission
        #submission2 = AnalysisPseudonym.get((assignment.analysis.id, pseudonym2)).submission
        
        submission1 = AnalysisPseudonym.query.filter_by(analysis=analysis).filter_by(pseudonym=pseudonym1).first().submission
        submission2 = AnalysisPseudonym.query.filter_by(analysis=analysis).filter_by(pseudonym=pseudonym2).first().submission


        #log.debug("%s %s %s %s %s" % (str(submission1), str(submission2), str(score1), str(score2), str(moss_analysis)))

        match = MossMatch(submission1=submission1, score1=int(score1),
                  submission2=submission2, score2=int(score2),
                  link=link,
                  mossAnalysis=moss_analysis)

        #log.debug(str(match))
    #shutil.copytree(moss_analysis.workDirectory, analysis.webDirectory)
    shutil.rmtree(moss_analysis.workDirectory) #clean up after ourselves
    shutil.rmtree(analysis.workDirectory) #clean up after ourselves
    del session['analysis_status']
    session.save()
    session.persist()
        
def submission_to_str(sub):
    if sub is None or not isinstance(sub, Submission):
        abort(404)
    if isinstance(sub, StudentSubmission):
        string = sub.student.netid+" "+str(sub.fileset.name) + " " + sub.fileset.offering.to_str()
        chopped = string.split(" ")
        return "_".join(chopped)
    elif isinstance(sub, SolutionSubmission):
        string =  "solution "+str(sub.fileset.name) + " " + sub.fileset.offering.to_str()
        chopped = string.split(" ")
        return "_".join(chopped)
    elif isinstance(sub, BaseSubmission):
        string =  "base "+str(sub.fileset.name) + " " + sub.fileset.offering.to_str()
        chopped = string.split(" ")
        return "_".join(chopped)

def submission_to_download_str(sub):
    if sub is None or not isinstance(sub, Submission):
        abort(404)
    if isinstance(sub, StudentSubmission):
        string = sub.student.netid+"/"+str(sub.fileset.name)
        chopped = string.split(" ")
        return "_".join(chopped)
    elif isinstance(sub, SolutionSubmission):
        string =  "solution/"+str(sub.fileset.name) 
        chopped = string.split(" ")
        return "_".join(chopped)
    elif isinstance(sub, BaseSubmission):
        string =  "base/"+str(sub.fileset.name) 
        chopped = string.split(" ")
        return "_".join(chopped)  
    
def fileset_id_string_to_id_list(string):
    try:
        return map(lambda x: int(x), string.split(','))
    except ValueError:
        return []