#!/usr/bin/env python

# Copyright 2010 Charlie Meyer <cemeyer2@illinois.edu>
# Based on original code copyright 2008 Alex Lambert <alex@alexlambert.com>

import sys, random, copy, os, subprocess, re, cgi, pickle, time
import pysvn, BeautifulSoup, pygraphviz, optparse

class Match:
        def __init__(self, student1, score1, student2, score2, link):
                self.student1 = student1
                self.score1 = int(score1)
                self.student2 = student2
                self.score2 = int(score2)
                self.link = link

        @property
        def is_solution(self):
                return (self.student1 == None) or (self.student2 == None)

	def __str__(self):
		s1 = self.student1
		if not s1:
			s1 = "solution"
		s2 = self.student2
		if not s2:
			s2 = "solution"
		return 'Match: ' + str(s1) + ', ' + str(s2)

class Student:
	def __init__(self, netid):
		self.netid = netid
		self.files = []

        def __str__(self):
                return self.netid

	@staticmethod
	def assignPseudonyms(studentList):
		studentListCopy = copy.copy(studentList)
		random.shuffle(studentListCopy)
		for index, student in enumerate(studentListCopy):
			student.pseudonym = str(index)

        @staticmethod
        def listFromRoster(rosterStream):
                return [Student(netid.strip()) for netid in rosterStream]

def main():
        parser = optparse.OptionParser()
        parser.add_option('--svnroot',
                          dest='svnroot',
                          metavar='URL',
                          help='sets the Subversion repository location')
        parser.add_option('--solution',
                          dest='solution',
                          metavar='PATH',
                          help='sets the solution path (relative to the Subversion root)')
        parser.add_option('--mp',
                          dest='mp',
                          metavar='NAME',
                          help='sets the MP name')
        parser.add_option('--partners',
                          dest='partners',
                          metavar='NAME',
                          help='sets the name of the partner list [default: %default]',
                          default='partners.txt')
        parser.add_option('--file',
                          dest='files',
                          action='append',
                          metavar='NAME',
                          help='considers this file in the student solution')
        parser.add_option('--roster',
                          dest='roster',
                          metavar='FILE',
                          help='sets the name of the roster')
        parser.add_option('--stage',
                          dest='stage',
                          metavar='STAGE',
                          help='starts the specified stage')

        (options, args) = parser.parse_args()

        # ./sigh.py --svnroot https://csil-projects.cs.uiuc.edu/svn/sp09/cs225 --mp mp5 --partners partners.txt --file quadtree.h --file quadtree.cpp --roster roster.tiny --solution "_course/_private/trunk/mp/Quadtrees/solution" --stage fetch

        if not options.svnroot:
                parser.error('Subversion root URL not specified')

        if not options.solution:
                parser.error('solution path not specified')

        if not options.mp:
                parser.error('MP name not specified')

        if not options.partners:
                parser.error('partners file not specified')

        if len(options.files) == 0:
                parser.error('no files specified')

        if not options.roster:
                parser.error('roster not specified')

        try:
                rosterStream = open(options.roster)
        except os.error:
                parser.error('could not open roster')

        if options.stage == 'fetch':
                try:
                        os.makedirs(options.mp)
                except os.error:
                        parser.error('MP directory already exists')

                fetch(options.svnroot, options.mp, rosterStream,
                           options.files, options.partners, options.solution)
        elif options.stage == 'moss':
                if not os.path.exists(options.mp):
                        parser.error('MP directory does not exist; run with fetch stage first')

                moss(options.svnroot, options.mp, rosterStream,
                          options.files, options.partners, options.solution)
        elif options.stage == 'analyze':
                if not os.path.exists(os.path.join(options.mp, 'moss')):
                        parser.error('MP directory does not have moss output; run with moss stage first')
                analyze(options.svnroot, options.mp, rosterStream,
                             options.files, options.partners, options.solution)
        else:
                parser.error('unknown stage')

def fetch(svnRoot, mpName, rosterStream, mpFiles, partnerFile, solutionPath):
        client = pysvn.Client()

        students = Student.listFromRoster(rosterStream)
        Student.assignPseudonyms(students)

        localSolutionPath = os.path.join(mpName, 'checkout', '_solution')
        os.makedirs(localSolutionPath)
        for mpFile in mpFiles:
                #sourcePath = '%s/%s/%s' % (svnRoot, solutionPath, mpFile)
                #EDIT
		sourcePath = 'https://csil-projects.cs.uiuc.edu/svn/sp09/cs225/%s%s' % (solutionPath, mpFile)
		destinationPath = os.path.join(localSolutionPath, mpFile)
                rev = pysvn.Revision( pysvn.opt_revision_kind.date, time.mktime(time.strptime("14 Nov 09", "%d %b %y")) )
		try:
                        print sourcePath
                        client.export(sourcePath, destinationPath, recurse=False, revision=rev)
                except pysvn.ClientError:
                        print "failed to fetch solution file %s\n" % (sourcePath)
                        return

        fetchFiles = mpFiles
        fetchFiles.append(partnerFile)

        for student in students:
                destinationDirectory = os.path.join(mpName, 'checkout', student.pseudonym)
                os.makedirs(destinationDirectory)

                for fetchFile in fetchFiles:
                        sourcePath = '%s/%s/%s/%s' % (svnRoot, student.netid, mpName, fetchFile)
                        destinationPath = os.path.join(destinationDirectory, fetchFile)

                        try:
                                print sourcePath
                                client.export(sourcePath, destinationPath, recurse=False)
                                student.files.append(destinationPath)
                                print '...fetched'
                        except pysvn.ClientError:
                                print '...failed'

        studentsStream = open(os.path.join(mpName, 'students'), 'w')
	try:
		pickle.dump(students, studentsStream)
	finally:
		studentsStream.close()

def moss(svnRoot, mpName, rosterStream, mpFiles, partnerFile, solutionPath):
	studentsStream = open(os.path.join(mpName, 'students'), 'r')
	try:
                students = pickle.load(studentsStream)
	finally:
		studentsStream.close()

        mossArgs = ['./moss', '-m', '40', '-l', 'cc', '-n', '250', '-d']
        mossArgs.extend([os.path.join(mpName, 'checkout', '_solution', mpFile) for mpFile in mpFiles])
        for student in students:
                mossArgs.extend(student.files)

        mossProcess = subprocess.Popen(mossArgs,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
        while True:
                output = mossProcess.stdout.readline().strip()
                if output.startswith('http://'):
                        mossURL = output
                elif output == '' and mossProcess.poll() != None:
                        break

        if not mossURL:
                print 'could not locate moss results'
                return

        mirrorPath = os.path.join(mpName, 'moss')
        os.makedirs(mirrorPath)

        wgetArgs = ['wget', '-nd', '-p', '-k', '-K', '-m',
                    '-P', mirrorPath, '--random-wait',
                    '--wait', '0', '-D', 'moss.stanford.edu',
                    '-np', mossURL]
        wgetProcess = subprocess.Popen(wgetArgs)
        if wgetProcess.wait() != 0:
                print 'could not run wget'
                return

def findMatches(mpName, students):
        resultsPath = os.path.join(mpName, 'moss', 'index.html')
	resultsStream = open(os.path.join(mpName, 'moss', 'index.html'))
	try:
                soup = BeautifulSoup.BeautifulSoup(resultsStream.read())
	finally:
		resultsStream.close()

        matches = []

        for row in soup.find('table').findAll('tr'):
                if row.find('th'):
                        continue

                studentData = row.findAll('a', limit=2)
                text1 = studentData[0].contents[0]
                text2 = studentData[1].contents[0]
                link = studentData[0]['href']

                # mp3/checkout/0/ (12%)
                textExp = re.compile(r'\w+/checkout/(\w+)/ \((\d+)%\)')
                (pseudonym1, score1) = textExp.match(text1).group(1, 2)
                (pseudonym2, score2) = textExp.match(text2).group(1, 2)

                student1 = student2 = None
                for student in students:
                        if student.pseudonym == pseudonym1:
                                student1 = student
                        elif student.pseudonym == pseudonym2:
                                student2 = student

                matches.append(Match(student1, score1, student2, score2, link))

        return matches

def analyze(svnRoot, mpName, rosterStream, mpFiles, partnerFile, solutionPath):
        studentsStream = open(os.path.join(mpName, 'students'), 'r')
	try:
                students = pickle.load(studentsStream)
	finally:
		studentsStream.close()

        matches = findMatches(mpName, students)

        resultsStream = open(os.path.join(mpName, 'results.html'), 'w')
	try:
                createResultsPage(mpName, partnerFile, resultsStream, matches, students)
	finally:
		resultsStream.close()
	
	#graphs with solution and student names
        print 'graph: thresh: 20 solution: T anonymous: F\n'
	createResultsGraph(mpName, matches, students, 20, True, False, 'results_thresh20_includeSolution_notAnonymous.gif')
	print 'graph: thresh: 30 solution: T anonymous: F\n'
	createResultsGraph(mpName, matches, students, 30, True, False, 'results_thresh30_includeSolution_notAnonymous.gif')
	print 'graph: thresh: 40 solution: T anonymous: F\n'
	createResultsGraph(mpName, matches, students, 40, True, False, 'results_thresh40_includeSolution_notAnonymous.gif')
	print 'graph: thresh: 50 solution: T anonymous: F\n'
        createResultsGraph(mpName, matches, students, 50, True, False, 'results_thresh50_includeSolution_notAnonymous.gif')

	#graphs without solution and with student name
	print 'graph: thresh: 20 solution: F anonymous: F\n'
	createResultsGraph(mpName, matches, students, 20, False, False, 'results_thresh20_noSolution_notAnonymous.gif')
        print 'graph: thresh: 30 solution: F anonymous: F\n'
	createResultsGraph(mpName, matches, students, 30, False, False, 'results_thresh30_noSolution_notAnonymous.gif')
        print 'graph: thresh: 40 solution: F anonymous: F\n'
	createResultsGraph(mpName, matches, students, 40, False, False, 'results_thresh40_noSolution_notAnonymous.gif')
	print 'graph: thresh: 50 solution: F anonymous: F\n'
        createResultsGraph(mpName, matches, students, 50, False, False, 'results_thresh50_noSolution_notAnonymous.gif')

	#graphs with solution and without student names
	print 'graph: thresh: 20 solution: T anonymous: T\n'
	createResultsGraph(mpName, matches, students, 20, True, True, 'results_thresh20_includeSolution_anonymous.gif')
        print 'graph: thresh: 30 solution: T anonymous: T\n'
	createResultsGraph(mpName, matches, students, 30, True, True, 'results_thresh30_includeSolution_anonymous.gif')
        print 'graph: thresh: 40 solution: T anonymous: T\n'
	createResultsGraph(mpName, matches, students, 40, True, True, 'results_thresh40_includeSolution_anonymous.gif')
	print 'graph: thresh: 50 solution: T anonymous: T\n'
        createResultsGraph(mpName, matches, students, 50, True, True, 'results_thresh50_includeSolution_anonymous.gif')

	#graphs without solution and without student names
	print 'graph: thresh: 20 solution: F anonymous: T\n'
	createResultsGraph(mpName, matches, students, 20, False, True, 'results_thresh20_noSolution_anonymous.gif')
        print 'graph: thresh: 30 solution: F anonymous: T\n'
	createResultsGraph(mpName, matches, students, 30, False, True, 'results_thresh30_noSolution_anonymous.gif')
        print 'graph: thresh: 40 solution: F anonymous: T\n'
	createResultsGraph(mpName, matches, students, 40, False, True, 'results_thresh40_noSolution_anonymous.gif')
	print 'graph: thresh: 50 solution: F anonymous: T\n'
        createResultsGraph(mpName, matches, students, 50, False, True, 'results_thresh50_noSolution_anonymous.gif')



def createResultsGraph(mpName, matches, students, threshold, includeSolution, anonymize, filename):
        graph = pygraphviz.AGraph()

        graph.graph_attr['label'] = mpName
        graph.graph_attr['overlap'] = 'scale' # false
        graph.graph_attr['splines'] = 'true'
	if includeSolution:
        	graph.add_node('[solution]', fillcolor='red', style='filled')
	if anonymize:
		for student in students:
			graph.add_node(student.pseudonym)
	else:
		graph.add_nodes_from(students)

        for match in matches:
		student1 = match.student1
                if not student1:
                        student1 = '[solution]'

                student2 = match.student2
                if not student2:
                        student2 = '[solution]'

                score = max(match.score1, match.score2)

		if includeSolution:
			if anonymize:
				if match.student1:
					student1 = student1.pseudonym
				if match.student2:
					student2 = student2.pseudonym
			if score >= threshold:
				graph.add_edge(student1, student2, label=str(score), penwidth=str(min(score / 10, 1)), length=str(min(100 - score,1)))
				
		if not match.is_solution and not includeSolution:
			if anonymize:
                        	student1 = student1.pseudonym
                                student2 = student2.pseudonym
                        if score >= threshold:
				graph.add_edge(student1, student2, label=str(score), penwidth=str(min(score / 10, 1)), length=str(min(100 - score,1)))

        graph.layout(prog='neato')	#was fdp
        graph.draw(os.path.join(mpName, filename))

def createResultsPage(mpName, partnerFile, resultsStream, matches, students):
        resultsStream.write('<h1>Results for %s</h1>' % cgi.escape(mpName))

        resultsStream.write('<h2>Solution matches</h2>')
        resultsStream.write('<table border="1">')

        for match in matches:
                if match.student1 and match.student2:
                        continue

                resultsStream.write('<tr>')

                if not match.student1:
                        resultsStream.write('<td>solution (%s%%)</td>' % match.score1)
                else:
                        resultsStream.write('<td><a href="checkout/%s/%s">%s</a> (%s%%)</td>'
                                            % (match.student1.pseudonym, partnerFile, match.student1.netid, match.score1))

                if not match.student2:
                        resultsStream.write('<td>solution (%s%%)</td>' % match.score2)
                else:
                        resultsStream.write('<td><a href="checkout/%s/%s">%s</a> (%s%%)</td>'
                                            % (match.student2.pseudonym, partnerFile, match.student2.netid, match.score2))

                resultsStream.write('<td><a href="%s">details</a></td>' % cgi.escape('moss/' + match.link))

                resultsStream.write('</tr>')

        resultsStream.write('</table>')
        resultsStream.write('<hr>')

        resultsStream.write('<h2>Peer-to-peer matches</h2>')
        resultsStream.write('<table border="1">')

        for match in matches:
                if not match.student1 or not match.student2:
                        continue

                resultsStream.write('<tr>')

                resultsStream.write('<td><a href="checkout/%s/partners.txt">%s</a> (%s%%)</td>'
                                        % (match.student1.pseudonym, match.student1.netid, match.score1))

                resultsStream.write('<td><a href="checkout/%s/partners.txt">%s</a> (%s%%)</td>'
                                        % (match.student2.pseudonym, match.student2.netid, match.score2))

                resultsStream.write('<td><a href="%s">details</a></td>' % cgi.escape('moss/' + match.link))

                resultsStream.write('</tr>')

        resultsStream.write('</table>')

if __name__ == "__main__":
	main()
