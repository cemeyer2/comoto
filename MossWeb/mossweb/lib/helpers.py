# -*- coding: utf-8 -*-
"""Helper functions

Consists of functions to typically be used within templates, but also
available to Controllers. This module is available to both as 'h'.
"""
# Import helpers as desired, or define your own, ie:
# from webhelpers.html.tags import checkbox, password
from webhelpers import *
from routes import url_for, redirect_to

# Scaffolding helper imports
from formbuild import start_with_layout as form_start, end_with_layout as form_end
from formbuild.helpers import field
from webhelpers.html.tags import *
from webhelpers.html import literal
from webhelpers.pylonslib import Flash
import sqlalchemy.types as types
from pylons.controllers.util import abort
from sqlalchemy.orm.exc import NoResultFound
from mossweb.model.model import User, Course, MossMatch, MossReportFile, Submission, SubmissionFile, Student, Image, StudentSubmission
import pysvn
from pysvn import ClientError
from tempfile import mkdtemp
import os
from pylons import config
import os.path
import threading
import Queue
import logging
from moss_helpers import __rand_string
from pylons import session
import time
import sys
from taskqueue import TaskQueue
from shutil import rmtree
from mossweb.lib.ldap_helpers import populate_user_from_active_directory
import re
from mossweb.model import Session
import urllib2


log = logging.getLogger(__name__)

flash = Flash()
# End of.

def get_object_or_404(model, **kw):
    """
    Returns object, or raises a 404 Not Found is object is not in db.
    Uses elixir-specific `get_by()` convenience function (see elixir source: 
    http://elixir.ematia.de/trac/browser/elixir/trunk/elixir/entity.py#L1082)
    Example: user = get_object_or_404(model.User, id = 1)
    """
    obj = model.get_by(**kw)
    if obj is None:
        abort(404)
    return obj

def get_user(environ):
    if not environ.has_key('HTTP_HTTP_X_FORWARDED_USER'):
        environ['HTTP_HTTP_X_FORWARDED_USER'] = "cemeyer2"
    userid = environ['HTTP_HTTP_X_FORWARDED_USER'].split("@")[0] #hack for bluestem auth, where the env variable is of the form netid@uiuc.edu/kerberos
    try:
        user = User.query.filter_by(name=userid).first()
        if not user:
            user = User(name=userid, superuser=False, enabled=False)
            populate_user_from_active_directory(user)
    except NoResultFound:
        user = User(name=userid, superuser=False, enabled=False)
        populate_user_from_active_directory(user)
    return user

def update_session(key, value, unique_id=""):
    session[key+unique_id] = value
    session.save()
    session.persist()

def get_from_session(key, unique_id=""):
    composite_key = key+unique_id
    if session.has_key(composite_key):
        return session[composite_key]
    return "Session Key Error"

def del_from_session(key, unique_id=""):
    composite_key = key+unique_id
    if session.has_key(composite_key):
        del session[composite_key]

def svn_export(svnroot, username, password, subdir, rev_time, special=False,unique_id=""):
    threadcount = 6
    #pool = Queue.Queue()
    #if sys.version_info < (2, 5):
    #    from taskqueue import TaskQueue
    #    pool = TaskQueue()
    pool = TaskQueue()
    export_total = -1
    update_session('import_status', "Started exporting "+svnroot+" for "+username+" with subdirectory "+subdir,unique_id)
    revision = pysvn.Revision( pysvn.opt_revision_kind.date, time.mktime(rev_time))
    #notify helper
    def notify( event_dict ):
        return
#        log.debug("pySVN Notify: "+str(event_dict))
    #helper function for ssl cert trust
    def ssl_server_trust_prompt( trust_dict ):
        return True, 1000, False
    #helper function to login to svn
    def get_login( realm, user, may_save ):
        return True, username, password, False
    #helper function to get a roster from svn
    def get_roster(svnRoot, username, password,unique_id):
        update_session('import_status', "Fetching roster from "+svnRoot+" for "+username,unique_id)
        client = pysvn.Client()
        client.exception_style = 1
        client.set_auth_cache(False)
        client.set_store_passwords(False)
        client.set_interactive(False)
        client.callback_get_login = get_login
        client.callback_ssl_server_trust_prompt = ssl_server_trust_prompt
        client.callback_notify = notify
        try:
            pathsListing = [result[0].repos_path.replace('/', '')
            for result in client.list(svnRoot, recurse=False)]
            netids = filter(lambda x: not x.startswith('_') and len(x) > 0,pathsListing)
            return netids
        except pysvn.ClientError, e:
            # print the whole message
            log.debug("ClientError: "+ str(e.args[0]))
            log.debug("Details: "+str(e.args[1]))
            raise e

        
    #thread to export from svn
    class ExportThread ( threading.Thread ):
        def __init__(self, svnroot=None, subdir=None, username=None, password=None, export_path=None, revision=None, session=None, special=False,unique_session_key_id=""):
            threading.Thread.__init__(self)
            self.svnroot = svnroot
            self.subdir = subdir
            self.username = username
            self.password = password
            self.export_path = export_path
            self.revision = revision
            self.session = session
            self.unique_id = unique_session_key_id

        def export(self, svnpath, username, password, destination):
            client = pysvn.Client()
            client.set_auth_cache(False)
            client.set_store_passwords(False)
            client.set_interactive(False)
            client.callback_get_login = get_login
            client.callback_ssl_server_trust_prompt = ssl_server_trust_prompt
            client.callback_notify = notify
            try:
                client.export(svnpath, destination, recurse=True, revision=self.revision)
            except pysvn.ClientError, e:
                log.debug("Error exporting "+svnpath+" to "+destination+" for "+username+": "+str(e))

        def run(self):
            if not special:
                while not pool.empty():
                    student = pool.get()
                    svndir = svnroot+"/"+student+"/"+self.subdir
                    destination = self.export_path+os.sep+student+os.sep
                    os.mkdir(destination)
                    destination = destination+self.subdir
                    log.debug("Exporting "+svndir+" to "+destination+" for "+self.username)
                    self.export(svndir, self.username, self.password, destination)
                    left = float(pool.qsize())
                    pct = 100 * ((export_total-left)/export_total)
                    pct = round(pct, 2)
                    self.session['import_status'+self.unique_id] = "SVN import: "+str(pct)+"% complete"
                    self.session.save()
                    self.session.persist()
                    pool.task_done()
            else:
                destination = self.export_path
                log.debug("Special Exporting "+svnroot+" to "+destination+" for "+self.username)
                self.export(svnroot, self.username, self.password, destination)
            log.debug("SVN export thread exiting")
    #end helper functions/classes
    roster = get_roster(svnroot, username, password,unique_id)
    export_total = float(len(roster))
    for student in roster:
        pool.put(student)
    tempdir = mkdtemp()
    update_session('import_status', "SVN import: initializing threads and starting export",unique_id)
    if not special:
        for i in range(threadcount):
            ExportThread(svnroot, subdir, username, password, tempdir,revision, session._current_obj(), special, unique_id).start()
        pool.join()
    else:
        rmtree(tempdir)
        thread = ExportThread(svnroot, "", username, password, tempdir, revision, session._current_obj(), special, unique_id)
        thread.start()
        thread.join()
    update_session('import_status', "Export of "+svnroot+" with subdirectory "+subdir+" to "+tempdir+" for "+username+" complete",unique_id)
    return tempdir

def try_svn_login(username, password, url):
    try_svn_login.attempts = 0
 
    def ssl_server_trust_prompt( trust_dict ):
        return True, 1000, False
    
    def get_login( realm, user, may_save ):
        try_svn_login.attempts += 1
        if try_svn_login.attempts > 1:
            raise Exception("Invalid Login Credentials")
        return True, username, password, False

    try:
        client = pysvn.Client()
        client.set_auth_cache(False)
        client.set_store_passwords(False)
        client.set_interactive(False)
        client.callback_get_login = get_login
        client.callback_ssl_server_trust_prompt = ssl_server_trust_prompt
        client.ls(url)
        return True
    except:
        return False

#recursively lists a directory
def lsdir(path):
    files = []
    def visit(prefix, dirname, names):
        for file in names:
            if not os.path.isdir(dirname+os.sep+file):
                files.append(dirname+os.sep+file)
    os.path.walk(path, visit, None)
    return files

def facebox(link_text, content, tooltip=""):
    div_id = __rand_string(32)
    link = literal("<a href='#"+div_id+"' rel='facebox' title='"+tooltip+"' >")+literal(link_text)+literal("</a>")
    div = "<div id='"+div_id+"' style='display:none;'>"+content+"</div>"
    return link+literal(div)

def facebox_ajax(link_text, target_url, tooltip=""):
    link = literal("<a href='"+target_url+"' rel='facebox' title='"+tooltip+"' >")+literal(link_text)+literal("</a>")
    return link

def extract_zip(zipfile, pwd):
    for f in zipfile.namelist():
        if f.endswith("/"):
            full_path = os.path.join(pwd, f)
            os.makedirs(full_path)
    for f in zipfile.namelist():
        if not f.endswith("/"):
            content = zipfile.read(f)
            full_path = os.path.join(pwd,f)
            try:
                os.makedirs(full_path[:full_path.rfind("/")])
            except:
                pass
	    outfile = open(full_path,"w")
            outfile.write(content)
            outfile.close()


def view_moss_result_url(mossmatch):
    if not isinstance(mossmatch, MossMatch) or mossmatch is None:
        abort(404)
    assignment = mossmatch.mossAnalysis.analysis.assignment
    report = assignment.report.mossReport
    file = get_object_or_404(MossReportFile, name=mossmatch.link, mossReport=report)
    return url_for(controller="view_analysis", action="view_moss_result", id=file.id)

def safe_unicode(string):
    try:
        unicode(string, "ascii")
    except UnicodeError:
        string = unicode(string, "utf-8")
    else:
        pass
    return string
            
def mossmatch_to_email_url(mossmatch):
    ids = []
    if mossmatch.submission1.row_type == 'studentsubmission':
        ids.append(str(mossmatch.submission1.student.id))
    if mossmatch.submission2.row_type == 'studentsubmission':
        ids.append(str(mossmatch.submission2.student.id))
    id_str = ",".join(ids)
    return url_for(controller='view_analysis', action='email_students', id=id_str, aid=mossmatch.mossAnalysis.analysis.assignment.id)

def mossmatch_to_email_url_ajax(mossmatch):
    ids = []
    if mossmatch.submission1.row_type == 'studentsubmission':
        ids.append(str(mossmatch.submission1.student.id))
    if mossmatch.submission2.row_type == 'studentsubmission':
        ids.append(str(mossmatch.submission2.student.id))
    id_str = ",".join(ids)
    return url_for(controller='view_analysis', action='email_students_ajax', id=id_str, aid=mossmatch.mossAnalysis.analysis.assignment.id)

def cluetip(link_text, title, content):
    div_id = __rand_string(32)
    link = "<a class='load-local' href='#"+div_id+"' rel='#"+div_id+"' title='"+title+"'>"+link_text+"</a>"
    div = "<div id='"+div_id+"' style='display:none;'>"+content+"</div>"
    return literal(link+div)

def cluetip_img(img_src, title, content):
    div_id = __rand_string(32)
    link = "<a class='load-local' href='#"+div_id+"' rel='#"+div_id+"' title='"+title+"' style='border-bottom: 0px dotted #CC0001; color: #FFFFFF'>"+img_src+"</a>"
    div = "<div id='"+div_id+"' style='display:none;'>"+content+"</div>"
    return literal(link+div)

def build_parse_partners_regex(fileset):
    regex = "("
    for sub in fileset.submissions:
        regex += sub.student.netid+"|"
    regex = regex[:-1]
    regex += ")"
    return regex 

def parse_partners(submission, regex_str = None):
    if submission is None or not isinstance(submission,Submission):
        abort(404)
    if submission.row_type != "studentsubmission":
        return
    student = submission.student
    if regex_str is None:
        regex_str = build_parse_partners_regex(submission.fileset)
    regex = re.compile(regex_str)
    for file in submission.submissionFiles:
        if file.meta or file.name == "partners.txt":
            content = file.content
            lines = content.split("\n")
            for line in lines:
                match = regex.search(line)
                if match:
                    for i in range(1, match.lastindex+1):
                        try:
                            partner_netid = match.group(i)
                            if partner_netid != student.netid:
                                try:
                                    partner = Student.query.filter_by(netid=partner_netid).all()[0]
                                    if partner not in submission.partners:
                                        submission.partners.append(partner)
                                        log.debug("adding "+partner.netid+" as a partner of "+student.netid)
                                        print "adding "+partner.netid+" as a partner of "+student.netid
                                except:
                                    pass
                        except:
                            pass
    Session.commit()
            
def partners_img(mossmatch):
    if mossmatch is None or not isinstance(mossmatch,MossMatch):
        abort(404)
    def is_partner_of(student, partner):
        if student.row_type != "studentsubmission" or partner.row_type != "studentsubmission":
            return False
        if partner.student in student.partners:
            return True
        return False
    left_url = url_for("/crystal_project/16x16/actions/1leftarrow.png")
    right_url = url_for("/crystal_project/16x16/actions/1rightarrow.png")
    no_url = url_for("/crystal_project/16x16/actions/cancel.png")
    title = "Partners"
    if is_partner_of(mossmatch.submission1, mossmatch.submission2) and is_partner_of(mossmatch.submission2, mossmatch.submission1):
        str = "<img src='"+left_url+"'/><img src='"+right_url+"'/>"
        #return literal(str)
        text = mossmatch.submission1.student.netid + " and "+mossmatch.submission2.student.netid+" declared each other as partners"
        return cluetip_img(str,title,text)
    elif is_partner_of(mossmatch.submission1, mossmatch.submission2):
        str = "<img src='"+right_url+"'/>"
        #return literal(str)
        text = mossmatch.submission1.student.netid + " declared "+mossmatch.submission2.student.netid+" as a partner, but not in reverse"
        return cluetip_img(str,title,text)
    elif is_partner_of(mossmatch.submission2, mossmatch.submission1):
        str = "<img src='"+left_url+"'/>"
        #return literal(str)
        text = mossmatch.submission2.student.netid + " declared "+mossmatch.submission1.student.netid+" as a partner, but not in reverse"
        return cluetip_img(str,title,text)
    else:
        str = "<img src='"+no_url+"'/>"
        #return literal(str)
        text = "Neither "+mossmatch.submission1.student.netid+" nor "+mossmatch.submission2.student.netid+" declared each other as partners"
        return cluetip_img(str, title, text)
    
def filter_moss_matches_to_minimum_score(matches, minimum_match_score=0):
    return filter(lambda match: match.score1 >= minimum_match_score or match.score2 >= minimum_match_score, matches)

#the next four functions need to be refactored DESPERATELY, they were hacked together in just a few hours 
def __get_api_signatures(method_name, include_types=True):
    from mossweb.controllers.api import ApiController
    from pylons.controllers import XMLRPCController
    import inspect
    log.debug("get_api_signatures: method: "+method_name)
    formal_method_name = method_name.replace(".","_")
    dict = ApiController.__dict__
    if not dict.has_key(formal_method_name):
        dict = XMLRPCController.__dict__
        if not dict.has_key(formal_method_name):
            return []
    method = dict[formal_method_name]
    signature = method.signature
    args_tuple = inspect.getargspec(method)
    args = args_tuple[0]
    defaults = args_tuple[3]
    
    def find_matching_signature(count):
        for sig in signature:
            if len(sig) == count:
                return sig
        return []
    #get method signatures
    signatures = []
    if defaults is None:
        #log.debug("finding matching signature")
        xmlrpc_sig = find_matching_signature(len(args))
        sig = method_name+"("
        for i in range(1,len(args)):
            sig += "<em>"+args[i]+"</em>"
            if include_types:
                sig += ": "+xmlrpc_sig[i]
            sig += ", "
        if len(args) > 1:
            sig = sig[:-2]
        sig += ")"
        signatures.append(sig)
    else:
        signature_count = 1 + len(defaults) #one signature using all defaults, and 1 sig for each additional default
        #get default signature
        #log.debug("finding matching signature")
        xmlrpc_sig = find_matching_signature(len(args) - len(defaults))
        sig = "<div style='width:1000px; z-index:1000'>"+method_name + "("
        for i in range(1, len(args) - len(defaults)):
            sig += "<em>"+args[i]+"</em>"
            if include_types:
                sig += ": "+xmlrpc_sig[i]
            sig += ", "
        if len(xmlrpc_sig) > 1:
            sig = sig[:-2]
        sig += ")"
        sig += "</div>"
        signatures.append(sig)
        #get all other signatures
        for j in range(1,signature_count):
            #log.debug("finding matching signature")
            xmlrpc_sig = find_matching_signature(len(args) - len(defaults)+j)
            sig = "<div style='width:1000px; z-index:1000'>"+method_name + "("
            for i in range(1, len(args) - len(defaults)+j):
                sig += "<em>"+args[i]+"</em>"
                if include_types:
                    sig += ": "+xmlrpc_sig[i]
                sig += ", "
            if len(xmlrpc_sig) > 1:
                sig = sig[:-2]
            sig += ")"
            sig += "</div>"
            signatures.append(sig)
    return signatures

def api_signature_links(method_name):
    signatures = __get_api_signatures(method_name, False) #no variable types on top links
    retval = ""
    for sig in signatures:
        retval += "<li>"
        retval += "<a href='#"+method_name+"'>"
        retval += sig
        retval += "</a>"
        retval += "</li>"
    return literal(retval)
    
def api_doc(method_name, args_list=[{}]):
    from mossweb.controllers.api import ApiController
    from pylons.controllers import XMLRPCController
    import inspect
    log.debug("api_doc: method: "+method_name)
    formal_method_name = method_name.replace(".","_")
    dict = ApiController.__dict__
    if not dict.has_key(formal_method_name):
        dict = XMLRPCController.__dict__
        if not dict.has_key(formal_method_name):
            return ""
    method = dict[formal_method_name]
    doc = method.__doc__.replace("\n", "")
    signature = method.signature
    
    signatures = __get_api_signatures(method_name)
    
    #get method return types
    return_types = []
    for sig in signature:
        if not sig[0] in return_types:
            return_types.append(sig[0])
    
    #create html docs
    retval = ""
    retval += "<a name='"+method_name+"'></a>"
    retval += "<p>"
    retval += "<h3>"+method_name+"</h3><br/>"
   
    retval += "<h4>Signature"+("", "s")[len(signatures) > 1]+"</h4>"
    retval += "<ul>"
    for sig in signatures:
        retval += "<li>"+sig+"</li>"
    retval += "</ul>"

    retval += "<h4>XML-RPC Return Type"+("","s")[len(return_types) > 1]+"</h4>"
    retval += "<ul>"
    for type in return_types:
        retval += "<li>"+type+"</li>"
    retval += "</ul>"
    
    retval += "<h4>Information</h4>"
    retval += doc
    

    retval += "<h4>Example Return Value"+("","s")[len(args_list) > 1]+"</h4>"
    for arg_dict in args_list:
        retval += api_example(method_name, arg_dict)
        
    retval += "</p>"
    retval += "<a href='#top'>top</a>"
    retval += "<br/><br/><br/><br/><br/><br/>"
    
    return literal(retval)

def api_example(method_name, arg_dict={}):
    from mossweb.controllers.api import ApiController
    from pylons.controllers import XMLRPCController
    import pprint
    from pylons import request
    import inspect

    log.debug("api_example: method: "+method_name)
    old_username = None
    if request.environ.has_key("'HTTP_HTTP_X_FORWARDED_USER"):
        old_username = request.environ['HTTP_HTTP_X_FORWARDED_USER']
        
    def restore_username():
        if old_username is not None:
            request.environ['HTTP_HTTP_X_FORWARDED_USER'] = old_username
    #give us superuser status
    request.environ['HTTP_HTTP_X_FORWARDED_USER'] = "cemeyer2"
    
    formal_method_name = method_name.replace(".", "_")
    d = ApiController.__dict__
    if not d.has_key(formal_method_name):
        d = XMLRPCController.__dict__
        if not d.has_key(formal_method_name):
            restore_username()
            return ""
    method = d[formal_method_name]
    signature = method.signature
    new_signature = []
    for lst in signature:
        tmp = []
        for item in lst:
            tmp.append(item)
        new_signature.append(tmp)
    args_tuple = inspect.getargspec(method)
    args = args_tuple[0]
    defaults = args_tuple[3]
    
    def find_matching_signature(count):
        for sig in new_signature:
            if len(sig) == count:
                return sig
        return []
    
    method_return_value = None
    i = 1
    max_tries = 10000
    xmlrpc_sig = find_matching_signature(len(args))
    pseudo_call_string = ""
    while True:
        call_string = "method.__call__(ApiController(), "
        pseudo_call_string = method_name+"("
        for j in range(1,len(args)):
            arg = args[j]
            #log.debug(arg)
            typ = xmlrpc_sig[j]
            if not arg_dict.has_key(arg) and (arg.endswith("_id") or arg == 'id'):
                call_string += str(i) + ", "
                pseudo_call_string += str(i) + ", "
            else:
                if arg_dict.has_key(arg):
                    default_arg_value = arg_dict[arg]
                    if type(default_arg_value) == str:
                        call_string += "\""+str(default_arg_value)+"\", "
                        pseudo_call_string += "\""+str(default_arg_value)+"\", "
                    else:
                        call_string += str(default_arg_value) + ", "
                        pseudo_call_string += str(default_arg_value) + ", "
                else:
                    break
        log.debug(method_name)
        log.debug("call_string: "+call_string)
        log.debug("pseudo_call_string: "+pseudo_call_string)
        log.debug("args: "+str(args))
        log.debug("arg_dict: "+str(arg_dict))
        if len(args)-len(arg_dict)>1:
            call_string = call_string[:-2]
            pseudo_call_string = pseudo_call_string[:-2]
        call_string += ")"
        pseudo_call_string += ")"
        #log.debug(call_string)
        method_return_value = eval(call_string)
        typ = type(method_return_value).__name__
        if typ == 'instance':
            typ = method_return_value.__class__.__name__
        if typ == 'Fault' or len(method_return_value) == 0:
            i = i+1
        else:
            break
        if i > max_tries:
            break
    
    def dict_to_string(d):
        #log.debug("dict: "+str(d))
        retval = {}
        for key in d.keys():
            #log.debug("key: "+key)
            act_val = d[key]
           # log.debug("act_val: "+str(act_val))
            val = ""
            if type(act_val) == dict:
                val = dict_to_string(act_val)
            elif type(act_val) == list:
                val = list_to_string(act_val)
            else:
                val = other_to_string(act_val)
            retval[key] = val
        #log.debug("returning: "+str(retval))
        return retval
        
    
    def list_to_string(l):
        #log.debug(str(l))
        retval = []
        if len(l) == 0:
            return retval
        else:
            for pop in l:
                if type(pop) == dict:
                    retval.append( dict_to_string(pop))
                elif type(pop) == list:
                    l#og.debug("in list")
                    retval.append( list_to_string(pop))
                else:
                    #log.debug("in other")
                    retval.append(other_to_string(pop))
                    #log.debug(retval)
        max = ""
        for item in retval:
            if len(str(item)) > len(str(max)):
                max = item
        return [max]
    
    def other_to_string(t):
        #log.debug("other")
        #log.debug(str(t))
        typ =  type(t).__name__
        if typ == 'instance':
            typ = t.__class__.__name__
        if typ == "long":
            typ = "int"
        if typ == "unicode":
            typ = "str"
        return typ
    
    #royal hacky kludge to fix stupid bug which erased method signatures
    if method_name == "system.methodSignature":
            method_return_value = eval(str(method_return_value))
            
    if type(method_return_value) == dict:
        formatted = pprint.pformat(dict_to_string(method_return_value))
    elif type(method_return_value) == list:
        formatted = pprint.pformat(list_to_string(method_return_value))
    else:
        formatted = other_to_string(method_return_value)
    
    #back to old permissions
    restore_username()
    
    formatted = formatted.replace("\n", "<br/>") #replace newlines with html line breaks 
    formatted = formatted.replace(" ", "&nbsp;") # replace spaces with html non-breaking spaces
    formatted = formatted.replace("'int'", "int") # get rid of the quotres around other types to denote that the value is of that type, not an actual string with value "string" or "int"
    formatted = formatted.replace("'str'", "string")
    formatted = formatted.replace("'bool'", "bool")
    formatted = formatted.replace("'DateTime'", "DateTime")
    formatted = formatted.replace("'Binary'", "Binary")
    
    retval = "Called as: <code>"+pseudo_call_string+"</code></br>"
    retval += "<pre>"
    retval += formatted
    retval += "</pre>"
    
    return retval

def format_file(file, format):
    """
    takes a submission file and formats it to the requested format
    returns a tuple (formatted_output, output_filename, mime_type) 
    """
    valid_formats = ["raw", "html", "latex", "png",  "jpeg", "bmp", "gif", "rtf", "svg"]
    if format not in valid_formats:
        raise AttributeError("format must be one of "+str(valid_formats))
    
    import mimetypes
    from pygments.lexers import guess_lexer_for_filename
    from pygments import highlight
    from pygments.formatters import HtmlFormatter, LatexFormatter, ImageFormatter, RtfFormatter, SvgFormatter
    from pygments.lexers import TextLexer

    if format == "raw":
        (type, encoding) = mimetypes.guess_type(file.name, False)
        if type is not None:
            mime = type
        else:
            #for some reason, python on centos doesnt pick up the same mimetypes as my computer does, even though they have the same version
            #of python installed, so this hack goes in here for now
            if file.name.lower().endswith(".cpp"):
                mime = "text/x-c++src"
            elif file.name.lower().endswith(".h"):
                mime = "text/x-chdr"
            elif file.name.lower().endswith(".java"):
                mime= "text/x-java"
            else:
                mime = "text/plain"
        return (str(file.content), file.name, mime)
    else: 
        lexer = None
        try:
            lexer = guess_lexer_for_filename(file.name, file.content)
        except:
            lexer = TextLexer()
            log.debug("could not automatically determine which lexer to use, defaulting to TextLexer")
        log.debug("lexer: "+ str(lexer))
       
        if format == "html":
            formatter = HtmlFormatter(full=True, linenos='table', nobackground=True)
            return (highlight(file.content, lexer, formatter), file.name+".html", "text/html")
        elif format == "latex":
            formatter = LatexFormatter(full=True, linenos=True, title=file.name)
            return (highlight(file.content, lexer, formatter), file.name+".tex", "text/x-tex")
        elif format == "png" or format=="gif" or format=="jpeg" or format=="bmp":
            filename = file.name+"."+format
            (type, encoding) = mimetypes.guess_type(filename, False)
            try:
                formatter = ImageFormatter(image_format=format)
                return (highlight(file.content, lexer, formatter), filename, type)
            except: #hack for my ubuntu install
                formatter = ImageFormatter(image_format=format, font_name="DejaVu Sans Mono")
                return (highlight(file.content, lexer, formatter), filename, type)
        elif format == "rtf":
            try:
                formatter = RtfFormatter()
                return (highlight(file.content, lexer, formatter), file.name+".rtf",  "application/rtf")
            except:
                #ubuntu hack
                formatter = RtfFormatter(fontface="DejaVu Sans Mono")
                return (highlight(file.content, lexer, formatter), file.name+".rtf",  "application/rtf")
        else:
            formatter = SvgFormatter()
            return (highlight(file.content, lexer, formatter), file.name+".svg",  'image/svg+xml')

def send_user_enabled_email(user):
    from turbomail import Message
    #send mail to user to notify them
    app_name = config['application_name']
    from_addr = config['error_email_from']
    suffix = config['email_suffix']
    to_addr = user.name + "@" + suffix
    subject = app_name+" user account request approved"         
    body = "Dear "+user.name+",\n\nYour request for an account on "+app_name+" has been approved.\n\n"
    body += "You can now login to https://comoto.cs.illinois.edu to begin using the application.\n\n"
    body += "Thanks\n\n"
    body += "The "+app_name+" Team\n\n\n\n"
    body += "Please do not reply to this message, as this account is not monitored"
    message = Message(from_addr, to_addr, subject)
    message.plain = body
    message.send()
    
def generate_histogram(assignment, title="Histogram"):
    log.debug("generating histogram")
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.colors as clrs
    from mossweb.model.model import SolutionSubmission, StudentSubmission
    ma = assignment.analysis.mossAnalysis
    matches = ma.matches
    l = []
#    for match in matches:
#        l.append(match.get_score())
    solution_matches = filter(lambda x: isinstance(x.submission1, SolutionSubmission) or isinstance(x.submission2, SolutionSubmission), matches)
    cross_semester_matches = filter(lambda x: isinstance(x.submission1, StudentSubmission) and isinstance(x.submission2, StudentSubmission) and x.submission1.offering.id != x.submission2.offering.id, matches)
    same_semester_matches = filter(lambda x: isinstance(x.submission1, StudentSubmission) and isinstance(x.submission2, StudentSubmission) and x.submission1.offering.id == x.submission2.offering.id, matches)
    sol_data = []
    for match in solution_matches:
        sol_data.append(match.get_score())
    same_data = []
    for match in same_semester_matches:
        same_data.append(match.get_score())
    cross_data = []
    for match in cross_semester_matches:
        cross_data.append(match.get_score())
    colors = []
    l.append(same_data)
    l.append(cross_data)
    l.append(sol_data)
    label = ['Same Semester', 'Cross Semester', 'Solution']
    plt.clf()
    plt.cla()
    plt.hist(l, bins=50, histtype='barstacked', label=label)
    plt.legend(loc='upper right')
    plt.ylabel('number of matches')
    plt.xlabel('match score')
    plt.title('Histogram of match scores')
    plt.savefig('/tmp/histogram.png', transparent=True)
    plt.close()
    fp = open('/tmp/histogram.png')
    data = fp.read()
    fp.close()
    os.remove('/tmp/histogram.png')
    i = Image(title=title, name="histogram", imageData=data, filename='histogram.png', type='png', owner_type="MossAnalysis", owner_id=ma.id)
    ma.images.append(i)
    Session.commit()
    
def anonymize_file_content(moss_report_file, moss_match):
    content = moss_report_file.content
    if isinstance(moss_match.submission1, StudentSubmission):
        content = __anonymize_file_content(content, moss_match.submission1.student)
    if isinstance(moss_match.submission2, StudentSubmission):
        content = __anonymize_file_content(content, moss_match.submission2.student)
    return content

def __anonymize_file_content(content, student):
    regex = re.compile(student.netid, re.DOTALL)
    matches = regex.finditer(content)
    for match in matches:
        start = match.start()
        end = match.end()
        old_text = content[start:end]
        content = content.replace(old_text, 'student'+str(student.id))
    return content
    
def get_icard_photo(student):
    fp = urllib2.urlopen('https://my.engr.illinois.edu/tools/viewphoto.asp?action=request_key')
    key = fp.read()
    fp = urllib2.urlopen('https://my.engr.illinois.edu/tools/viewphoto.asp?id='+student.netid+'&key='+key)
    photo = fp.read()
    if len(photo) > 0:
        images = Image.query.filter_by(owner_id=student.id).filter_by(owner_type="Student").all()
        found = False
        for image in images:
            if image.imageData == photo:
                found = True
        if not found:
            i = Image(title="I-Card Photo", name="icardphoto", imageData=photo, filename=student.netid+'-icard.jpg', type='jpg', owner_type="Student", owner_id=student.id)
            Session.commit()
        return photo
    else:
        image = Image.query.filter_by(owner_id=student.id).filter_by(owner_type="Student").order_by("id DESC").first()
        if image is not None:
            return image.imageData
        cwd = os.getcwd()
        fp = open(os.path.join(cwd, "mossweb", "public", "NA.jpg"))
        photo = fp.read()
        fp.close()
        return photo