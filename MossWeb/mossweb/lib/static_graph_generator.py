'''
Created on Oct 25, 2010

@author: chuck
'''
from mossweb.model.model import Assignment, MossMatch, StaticMossGraph, MossReport, User
import pygraphviz
import threading
from mossweb.lib.taskqueue import TaskQueue
import logging
from mossweb.model import Session
from mossweb.lib import helpers as h
import imghdr
from PIL import Image
import os
import traceback
from pylons import request
from pylons import config
from turbomail import Message

log = logging.getLogger(__name__)

class StaticGraphProcessor:
    queue = None
    
    class Processor(threading.Thread):
    
        def __init__(self):
            threading.Thread.__init__(self)
            self.shouldRun = True
        
        def run(self):
            while self.shouldRun:
                try:
                    user_id,assignment_id,threshold,includeSolution,anonymize,singletons,layoutEngine,environ = StaticGraphProcessor.queue.get(True, 5)
                    assignment = h.get_object_or_404(Assignment, id=assignment_id)
                    user = h.get_object_or_404(User,id=user_id)
                    try:
                        self.create_static_graph2(user,assignment, threshold, includeSolution, anonymize, singletons, layoutEngine)
                    except Exception, e:
                        msg = "failed to create static graph: "+str(e)
                        print msg
                        log.warning(msg)
                        tb = traceback.format_exc()
                        log.warn(tb)
                        self.mail_admin_error(user, assignment, tb, environ, includeSolution, anonymize, singletons, layoutEngine)
                        self.mail_user_error(user)
                    StaticGraphProcessor.queue.task_done()
                except Exception, e:
                    pass
            log.debug("processor dying")
        
        def kill(self):
            self.shouldRun = False
            
        def mail_admin_error(self,user, assignment, tb, environ, includeSolution, anonymize, singletons, layoutEngine):
            from pprint import pformat
            app_name = config['application_name']
            from_addr = config['error_email_from']
            to_addr = config['email_to']
            subject = "Error generating static graph"
            body = "Error generating static graph\n\n"
            body += tb+"\n\n"
            body += pformat(environ) + "\n\n"
            body += "user: "+str(user)+" -- id: "+str(user.id)+"\n"
            body += "assignment: "+str(assignment)+" -- id: "+str(assignment.id)+"\n"
            body += "includeSolution: "+str(includeSolution)+"\n"
            body += "anonymize: "+str(anonymize)+"\n"
            body += "singletons: "+str(singletons)+"\n"
            body += "layoutEngine: "+str(layoutEngine)+"\n"
            message = Message(from_addr, to_addr, subject)
            message.plain = body
            message.send
        
        def mail_user_error(self, user):
            app_name = config['application_name']
            from_addr = config['error_email_from']
            suffix = config['email_suffix']
            to_addr = user.name + "@" + suffix
            subject = app_name+" static moss analysis graph generation failed"         
            body = "Dear "+user.name+",\n\nThe static moss analysis graph that you requested is failed to generate.\n\n"
            body += "The "+app_name+" developers have been informed of this error and will correct it as soon as possible.\n\n"
            body += "Thanks\n\n"
            body += "The "+app_name+" Team\n\n\n\n"
            body += "Please do not reply to this message, as this account is not monitored"
            message = Message(from_addr, to_addr, subject)
            message.plain = body
            message.send()
                      
        def mail_user(self,graph):
            app_name = config['application_name']
            from_addr = config['error_email_from']
            suffix = config['email_suffix']
            to_addr = graph.requestingUser.name + "@" + suffix
            subject = app_name+" static moss analysis graph generation complete"         
            body = "Dear "+graph.requestingUser.name+",\n\nThe static moss analysis graph that you requested is now complete and ready for viewing.\n\n"
            body += "Assignment: "+str(graph.assignment.course.name)+ " " + str(graph.assignment.name)+"\n\n"
            body += "Details: "+graph.to_str()+"\n\n"
            body += "You can now login to "+app_name+" to view your graph on the view analysis page where you requested it.\n\n"
            body += "Thanks\n\n"
            body += "The "+app_name+" Team\n\n\n\n"
            body += "Please do not reply to this message, as this account is not monitored"
            message = Message(from_addr, to_addr, subject)
            message.plain = body
            message.send()
            
        def create_static_graph2(self,user,assignment,threshold=0,includeSolution=True,anonymize=False,singletons=False,layout_engine='neato'):
            if layout_engine not in ['dot','neato','fdp','sfdp','twopi','circo', 'sfdp']:
                raise AssertionError("invalid layout engine")
            
            staticMossGraph = StaticMossGraph()
            staticMossGraph.assignment = assignment
            staticMossGraph.threshold = threshold
            staticMossGraph.includeSolution = includeSolution
            staticMossGraph.anonymize = anonymize
            staticMossGraph.singletons = singletons
            staticMossGraph.layoutEngine = layout_engine
            staticMossGraph.isComplete = False
            staticMossGraph.requestingUser = user
            
            graph = pygraphviz.AGraph()
        
            graph.graph_attr['label'] = assignment.course.name + " " + assignment.name
            graph.graph_attr['overlap'] = 'scale' # false
            graph.graph_attr['splines'] = 'true'
            graph.graph_attr['overlap'] ="prism"
            
            matches = assignment.analysis.mossAnalysis.matches
            pseudo_dict = self.generate_pseudonym_dict(assignment,anonymize)
            
            for key in pseudo_dict:
                graph.add_node(pseudo_dict[key])
            
            graph = self.add_edges_to_graph(assignment,graph,pseudo_dict,threshold, includeSolution, anonymize)
            
            if singletons == False:
               graph = self.remove_singletons(graph)
            #graph.write("/tmp/graph_nolayout.dot")
            self.render_graph(graph, layout_engine,staticMossGraph)
        
        def remove_singletons(self, graph):
            for node in graph.nodes():
                if len(graph.neighbors(node)) == 0:
                    graph.delete_node(node)
            return graph
                
        def add_edges_to_graph(self, assignment, graph, pseudo_dict,threshold, include_solution, anonymize):
            
            def add_edge(match):
                score = match.get_score()
                if score < threshold:
                    return
                sub1_partner_of_sub2 = self.is_partner_of(match.submission1, match.submission2)
                sub2_partner_of_sub1 = self.is_partner_of(match.submission2, match.submission1)
                dirType = "none"
                color = "black"
                if sub1_partner_of_sub2 == True and sub2_partner_of_sub1==False:
                    dirType = "forward"
                    color = "yellow"
                elif sub2_partner_of_sub1==True and sub1_partner_of_sub2 == False:
                    dirType = "back"
                    color = "yellow"
                elif sub1_partner_of_sub2==True and sub2_partner_of_sub1==True:
                    dirType = "both"
                    color = "green"
                graph.add_edge(pseudo_dict[self.pseudo_dict_key(match.submission1, anonymize)], pseudo_dict[self.pseudo_dict_key(match.submission2, anonymize)], label=str(score),dirType=dirType,color=color)                    
            
            pruned = assignment.analysis.mossAnalysis.pruned
            student_only_matches = filter(lambda match: match.submission1.row_type=='studentsubmission' and match.submission2.row_type=='studentsubmission', assignment.analysis.mossAnalysis.matches)
            solution_matches = []
            if include_solution:
                solution_matches = filter(lambda match: (match.submission1.row_type=='solutionsubmission') ^ (match.submission2.row_type=='solutionsubmission'), assignment.analysis.mossAnalysis.matches)
            if pruned:
                pruned_offering = assignment.analysis.mossAnalysis.prunedOffering
                pruned_only_matches = filter(lambda match: match.submission1.offering==pruned_offering and match.submission2.offering==pruned_offering, student_only_matches)
                sub1_pruned_sub2_not_matches = filter(lambda match: match.submission1.offering==pruned_offering and match.submission2.offering!=pruned_offering, student_only_matches)
                sub2_pruned_sub1_not_matches = filter(lambda match: match.submission2.offering==pruned_offering and match.submission1.offering!=pruned_offering, student_only_matches)
                for match in pruned_only_matches:
                    add_edge(match)
                for match in sub1_pruned_sub2_not_matches:
                    score = match.get_score()
                    if score >= threshold:
                        node = graph.get_node(pseudo_dict[self.pseudo_dict_key(match.submission1, anonymize)])
                        node.attr['fillcolor'] = "#FFFF00"
                        node.attr['style'] = 'filled'
                for match in sub2_pruned_sub1_not_matches:
                    score = match.get_score()
                    if score >= threshold:
                        node = graph.get_node(pseudo_dict[self.pseudo_dict_key(match.submission2, anonymize)])
                        node.attr['fillcolor'] = "#FFFF00"
                        node.attr['style'] = 'filled'
            else:
                for match in student_only_matches:
                    add_edge(match)
                    
            
            for match in solution_matches:                
                if match.submission1.row_type == 'studentsubmission':
                    if match.get_score >= threshold:
                        key = self.pseudo_dict_key(match.submission1, anonymize)
                        if graph.has_node(key):
                            node = graph.get_node(key)
                            node.attr['fillcolor'] = "#FF0000"
                            node.attr['style'] = 'filled'
                elif match.submission2.row_type == 'studentsubmission':
                    if match.get_score() >= threshold:
                        key = self.pseudo_dict_key(match.submission2, anonymize)
                        if graph.has_node(key):
                            node = graph.get_node(key)
                            node.attr['fillcolor'] = "#FF0000"
                            node.attr['style'] = 'filled'
            
            return graph
        
        def is_partner_of(self, student, partner):
            if student.row_type != "studentsubmission" or partner.row_type != "studentsubmission":
                return False
            if partner.student in student.partners:
                return True
            return False
        
        def pseudo_dict_key(self, submission, anonymize):
            if not anonymize:
                return (submission.student.netid+" "+submission.fileset.offering.semester.to_str()).encode('UTF-8')
            else:
                return (str(submission.id)+" "+submission.fileset.offering.semester.to_str()).encode('UTF-8')
        
        def generate_pseudonym_dict(self, assignment, anonymize):
            pseudo_dict = {}
            pruned = assignment.analysis.mossAnalysis.pruned
            sets = filter(lambda fs: fs.row_type=='fileset', assignment.filesets)
            
            def add_fileset_to_dict(fs, anonymize):
                for submission in fs.submissions:
                    key = self.pseudo_dict_key(submission, anonymize)
                    if anonymize:
                        pseudo_dict[key] = (str(submission.id)+" "+submission.fileset.offering.semester.to_str()).encode('UTF-8')
                    else:
                        pseudo_dict[key] = key.encode('UTF-8')
                    
            if pruned:
                pruned_offering = assignment.analysis.mossAnalysis.prunedOffering
                for fileset in sets:
                    if fileset.offering == pruned_offering:
                        add_fileset_to_dict(fileset, anonymize)
            else:
                for fileset in sets:
                    add_fileset_to_dict(fileset, anonymize)
            return pseudo_dict
        
        def render_graph(self, graph, layout_engine, staticMossGraph):
            graph.layout(prog=layout_engine)    #was fdp
            #graph.draw("/tmp/graph.dot")
            graph.draw("/tmp/graph.png", args='-Tpng:gd:gd ')
            image = Image.open('/tmp/graph.png')
            image.thumbnail((150,150), Image.ANTIALIAS)
            image.save('/tmp/graph-thumbnail.png')
            
            image2 = Image.open('/tmp/graph.png')
            width,height = image2.size
            image2.thumbnail((int(width*.3),int(height*.3)), Image.ANTIALIAS)
            image2.save('/tmp/graph-medium.png')
            try:
                f = open('/tmp/graph.png', 'r')
                data = f.read()
                staticMossGraph.imageData = data
                f.close()
                f2 = open('/tmp/graph-thumbnail.png')
                data2 = f2.read()
                f2.close()
                staticMossGraph.thumbnailData = data2
                f3 = open('/tmp/graph-medium.png')
                data3 = f3.read()
                f3.close()
                staticMossGraph.mediumData = data3                
                staticMossGraph.isComplete = True
                self.mail_user(staticMossGraph)
            except Exception, e:
                pass
            try:               
                os.remove('/tmp/graph.png')
                pass
            except Exception, e:
                msg = "failed to remove graph.png: "+str(e)
                log.warning(msg)
                print msg
            try:
                os.remove('/tmp/graph-thumbnail.png')
            except Exception, e:
                msg = "failed to remove graph-thumbnail.png: "+str(e)
                log.warning(msg)
                print msg
            try:
                os.remove('/tmp/graph-medium.png')
            except Exception, e:
                msg = "failed to remove graph-medium.png: "+str(e)
                log.warning(msg)
                print msg
            Session.commit()
                    
        def create_static_graph(self, user,assignment, threshold=0, includeSolution=True, anonymize=False, singletons=False, layout_engine='neato'):
            
            if layout_engine not in ['dot','neato','fdp','sfdp','twopi','circo', 'sfdp']:
                raise AssertionError("invalid layout engine")
            
            staticMossGraph = StaticMossGraph()
            staticMossGraph.assignment = assignment
            staticMossGraph.threshold = threshold
            staticMossGraph.includeSolution = includeSolution
            staticMossGraph.anonymize = anonymize
            staticMossGraph.singletons = singletons
            staticMossGraph.layoutEngine = layout_engine
            staticMossGraph.isComplete = False
            staticMossGraph.requestingUser = user
            
            graph = pygraphviz.AGraph()
        
            graph.graph_attr['label'] = assignment.course.name + " " + assignment.name
            graph.graph_attr['overlap'] = 'scale' # false
            graph.graph_attr['splines'] = 'true'
            if includeSolution:
                for fileset in assignment.filesets:
                    if fileset.row_type=="solutionfileset":
                        graph.add_node('[solution]', fillcolor='red', style='filled')
            mossMatches = assignment.analysis.mossAnalysis.matches
            pseudonyms = {}
            i = 0
            pruned_offering = None
            if assignment.analysis.mossAnalysis.pruned:
                pruned_offering = assignment.analysis.mossAnalysis.get_pruned_offering()
            def pseudo_dict_key(submission):
                return submission.student.netid+" "+submission.fileset.offering.semester.to_str()
            
            def add_submission_to_dict(submission):
                if not pseudonyms.has_key(submission.student.netid):
                    if anonymize:
                        pseudonyms[pseudo_dict_key(submission)] =  (str(i)+" "+submission.fileset.offering.semester.to_str()).encode('UTF-8')
                        i = i+1
                    else:
                        pseudonyms[pseudo_dict_key(submission)] = pseudo_dict_key(submission).encode('UTF-8')
                    
            for fileset in assignment.filesets:
                if fileset.row_type == 'fileset' and pruned_offering is None:
                    for submission in fileset.submissions:
                        add_submission_to_dict(submission)
                elif fileset.row_type == 'fileset' and fileset.offering == pruned_offering:
                    for submission in fileset.submissions:
                        add_submission_to_dict(submission)
                        
            for netid in pseudonyms:
                graph.add_node(pseudonyms[netid])
                
            for match in mossMatches:
                student1 = None
                student2 = None
                color="black"
                if match.submission1.row_type == "studentsubmission":
                    if pseudonyms.has_key(pseudo_dict_key(match.submission1)):
                        student1 = pseudonyms[pseudo_dict_key(match.submission1)]
                else:
                    student1 = "[solution]"
                if match.submission2.row_type == "studentsubmission":
                    if pseudonyms.has_key(match.submission2):
                        student2 = pseudonyms[match.submission2]
                else:
                    student2 = "[solution]"
                
                def is_partner_of(student, partner):
                    if student.row_type != "studentsubmission" or partner.row_type != "studentsubmission":
                        return False
                    if partner.student in student.partners:
                        return True
                    return False
                
                color = "black"
                if match.submission1.row_type == 'studentsubmission' and match.submission2.row_type == 'studentsubmission':
                    if is_partner_of(match.submission1, match.submission2) and is_partner_of(match.submission2, match.submission1):
                        color = "green"
                    elif is_partner_of(match.submission1, match.submission2):
                        color = "yellow"
                    elif is_partner_of(match.submission2, match.submission1):
                        color = "yellow"
                
                score = match.get_score()
                if score >= threshold and student1 is not None and student2 is not None:
                    if not includeSolution and match.submission1.row_type != 'solutionsubmission' and match.submission2.row_type != 'solutionsubmission':
                        graph.add_edge(student1, student2, label=str(score), color=color, penwidth=str(min(score / 10, 5)), len=str(min(100 - score,1)))
                    elif includeSolution:
                        graph.add_edge(student1, student2, label=str(score), color=color, penwidth=str(min(score / 10, 5)), len=str(min(100 - score,1)))
                elif student1 is None and student2 is not None: #student2 matches previous semester
                    log.debug("student2 matches prev semester student1")
                    log.debug("student1: "+str(student1))
                    log.debug("student2: "+str(student2))
                    node = graph.get_node(student2)
                    node.attr['color'] = "#FFFF00"
                elif student1 is not None and student2 is None: #student1 matches previous semester
                    log.debug("student1 matches prev semester student2")
                    log.debug("student1: "+str(student1))
                    log.debug("student2: "+str(student2))
                    node = graph.get_node(student1)
                    node.attr['color'] = "#FFFF00"
            
            if singletons == False:
                for netid in pseudonyms:
                    if len(graph.neighbors(pseudonyms[netid])) == 0:
                        graph.delete_node(pseudonyms[netid])
                        
            graph.layout(prog=layout_engine)    #was fdp
            graph.draw("/tmp/graph.png", args='-Tpng:gd:gd ')
            image = Image.open('/tmp/graph.png')
            image.thumbnail((150,150), Image.ANTIALIAS)
            image.save('/tmp/graph-thumbnail.png')
            
            image2 = Image.open('/tmp/graph.png')
            width,height = image2.size
            image2.thumbnail((int(width*.3),int(height*.3)), Image.ANTIALIAS)
            image2.save('/tmp/graph-medium.png')
            try:
                f = open('/tmp/graph.png', 'r')
                data = f.read()
                staticMossGraph.imageData = data
                f.close()
                f2 = open('/tmp/graph-thumbnail.png')
                data2 = f2.read()
                f2.close()
                staticMossGraph.thumbnailData = data2
                f3 = open('/tmp/graph-medium.png')
                data3 = f3.read()
                f3.close()
                staticMossGraph.mediumData = data3                
                staticMossGraph.isComplete = True
                self.mail_user(staticMossGraph)
            except Exception, e:
                pass
            try:               
                os.remove('/tmp/graph.png')
            except Exception, e:
                msg = "failed to remove graph.png: "+str(e)
                log.warning(msg)
                print msg
            try:
                os.remove('/tmp/graph-thumbnail.png')
            except Exception, e:
                msg = "failed to remove graph-thumbnail.png: "+str(e)
                log.warning(msg)
                print msg
            try:
                os.remove('/tmp/graph-medium.png')
            except Exception, e:
                msg = "failed to remove graph-medium.png: "+str(e)
                log.warning(msg)
                print msg
            Session.commit()

    class __impl:
    
        processor = None
            
        def __init__(self):
            StaticGraphProcessor.queue = TaskQueue()
            self.processor = StaticGraphProcessor.Processor()
            self.processor.start()
        
        def add_static_graph_to_queue(self, assignment, **kwargs):
            threshold=0
            includeSolution=True
            anonymize=False
            singletons=False
            layoutEngine ='neato'
            if kwargs.has_key("threshold"):
                threshold = kwargs['threshold']
            if kwargs.has_key("includeSolution"):
                includeSolution = kwargs['includeSolution']
            if kwargs.has_key("anonymize"):
                anonymize = kwargs['anonymize']
            if kwargs.has_key("singletons"):
                singletons = kwargs['singletons']
            if kwargs.has_key("layoutEngine"):
                layoutEngine = kwargs['layoutEngine']
            user = h.get_user(request.environ)      
            StaticGraphProcessor.queue.put((user.id,assignment.id,threshold,includeSolution,anonymize,singletons,layoutEngine, request.environ))          
        
        def get_number_of_graphs_in_queue(self):
            return StaticGraphProcessor.queue.qsize()
        
        def kill_processor(self):
            self.processor.kill()

    __instance = None
    
    def __init__(self):
        if StaticGraphProcessor.__instance is None:
            StaticGraphProcessor.__instance = StaticGraphProcessor.__impl()
        self.__dict__['_Singleton__instance'] = StaticGraphProcessor.__instance
    
    def __getattr__(self, attr):
        return getattr(self.__instance, attr)
    
    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)