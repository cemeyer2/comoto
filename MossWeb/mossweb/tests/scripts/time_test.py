import timeit

iterations = 2
netid = 'cemeyer2'
password = 'password'

def get_server():
	import xmlrpclib	
	#srvr = xmlrpclib.Server('https://'+netid+':'+password+'@comoto.cs.illinois.edu/comoto/api')
	srvr = xmlrpclib.Server('http://localhost:5000/api')
	return srvr

def getCourses():
	srvr = get_server()
	srvr.getCourses()

def getAssignment():
	srvr = get_server()
	srvr.getAssignment(65)

def getAnalysis():
	srvr = get_server()
	srvr.getAnalysis(64)

def getMossAnalysis():
	srvr = get_server()
	srvr.getMossAnalysis(62, True)
	
def getFileSet():
	srvr = get_server()
	for id in [2, 3, 4, 8, 83, 84, 125, 127]:
		srvr.getFileSet(id, True, True)
		
def getStudent():
	srvr = get_server()
	for id in range(1,1000):
		try:
			srvr.getStudent(id, True)
		except:
			pass

setup = 'from __main__ import getCourses, getAssignment, getAnalysis, getMossAnalysis, getFileSet, getStudent'

#stmt = 'getCourses()'
#t = timeit.Timer(stmt, setup)
#get_courses_time = t.timeit(number=iterations)/iterations
#
#stmt = 'getAssignment()'
#t = timeit.Timer(stmt, setup)
#get_assignment_time = t.timeit(number=iterations)/iterations
#
#stmt = 'getAnalysis()'
#t = timeit.Timer(stmt, setup)
#get_analysis_time = t.timeit(number=iterations)/iterations
#
#stmt = 'getMossAnalysis()'
#t = timeit.Timer(stmt, setup)
#get_moss_analysis_time = t.timeit(number=iterations)/iterations
#
#stmt = 'getFileSet()'
#t = timeit.Timer(stmt, setup)
#get_fileset_time = t.timeit(number=iterations)/iterations
#
#total_time = get_courses_time + get_assignment_time + get_analysis_time + get_moss_analysis_time + get_fileset_time
#
#print "getCourses():      "+str(get_courses_time)
#print "getAssignment():   "+str(get_assignment_time)
#print "getAnalysis():     "+str(get_analysis_time)
#print "getMossAnalysis(): "+str(get_moss_analysis_time)
#print "getFileSet():      "+str(get_fileset_time)
#print "total time:        "+str(total_time)

stmt = 'getStudent()'
t = timeit.Timer(stmt, setup)
print str( t.timeit(number=iterations)/iterations)