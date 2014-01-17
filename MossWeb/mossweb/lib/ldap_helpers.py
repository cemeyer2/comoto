'''
Created on Oct 13, 2010

@author: chuck
'''

from mossweb.model.model import Student, User, Course
from mossweb.model import Session
import ldap
from ldap.controls import SimplePagedResultsControl
import logging, re
import pprint
from pylons import config

log = logging.getLogger(__name__)

class LDAPRunner:
    
    class __impl:           
         
        def __init__(self, host, directory_host, who, cred):
            self.host = host
            self.directory_host = directory_host
            self.cred = cred
            self.who = who
            self.page_size = 250
        
        def orFilter(self, cn_list):
            if len(cn_list) == 0:
                return ""
            if len(cn_list) == 1:
                return "("+cn_list[0]+")"
            filter = "(|"
            for cn in cn_list:
                filter += "("+cn+")"
            filter += ")"
            return filter

        def andFilter(self, cn_list):
            if len(cn_list) == 0:
                return ""
            if len(cn_list) == 1:
                return "("+cn_list[0]+")"
            filter = "(&"
            for cn in cn_list:
                filter += "("+cn+")"
            filter += ")"
            return filter

        def notFilter(self, cn_list):
            if len(cn_list) == 0:
                return ""
            filter = "(!"
            for cn in cn_list:
                filter += "("+cn+")"
            filter += ")"
            return filter
        
        def get_ldap_host(self):
            return self.host
        
        def get_directory_host(self):
            return self.directory_host     

        def run_search(self, search_base, search_filter, attrs=None, **kwargs):
            host = self.host
            who = self.who
            cred = self.cred
            scope = ldap.SCOPE_SUBTREE
            if kwargs.has_key("host"):
                host = kwargs['host']
            if kwargs.has_key("who"):
                who = kwargs['who']
            if kwargs.has_key('cred'):
                cred = kwargs['cred']
            if kwargs.has_key('scope'):
                scope = kwargs['scope']
            if host is not self.get_ldap_host() and host is not self.get_directory_host():
                raise Exception("Invalid host, must use either ldap host or directory host")
            scope_str = "ldap.SCOPE_SUBTREE"
            if scope == ldap.SCOPE_BASE:
                scope_str = 'ldap.SCOPE_BASE'
            elif scope == ldap.SCOPE_ONELEVEL:
                scope_str = 'ldap.SCOPE_ONELEVEL'
            log.debug("running search")
            log.debug("host: "+host)
            log.debug("who: "+who)
            log.debug("base: "+search_base)
            log.debug("filter: "+search_filter)
            log.debug("attrs: "+str(attrs))
            log.debug('scope: '+scope_str)
            try:
                conn = ldap.initialize(host)
                ldap.set_option( ldap.OPT_X_TLS_DEMAND, True )
                #ldap.set_option( ldap.OPT_DEBUG_LEVEL, 255 )
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT,ldap.OPT_X_TLS_NEVER)
                if host is self.get_ldap_host():
                    result = conn.simple_bind_s(who,cred)
                else:
                    result = conn.simple_bind_s()
                result = conn.search_s( search_base, scope, search_filter, attrs )
                conn.unbind()
                return result
            except ldap.LDAPError, e:
                import traceback
                log.error("run_search error:")
                log.error(traceback.format_exc())
                log.error(str(e))
                try:
                    conn.unbind()
                except:
                    pass
                return []

        #adapted from http://www.novell.com/coolsolutions/tip/18274.html
        def run_paged_search(self, search_base, search_filter, attrs=None, **kwargs):
            host = self.host
            who = self.who
            cred = self.cred
            page_size = self.page_size
            scope = ldap.SCOPE_SUBTREE
            if kwargs.has_key("host"):
                host = kwargs['host']
            if kwargs.has_key("who"):
                who = kwargs['who']
            if kwargs.has_key('cred'):
                cred = kwargs['cred']
            if kwargs.has_key('scope'):
                scope = kwargs['scope']
            if kwargs.has_key("page_size"):
                page_size = int(kwargs['page_size'])
            scope_str = "ldap.SCOPE_SUBTREE"
            if scope == ldap.SCOPE_BASE:
                scope_str = 'ldap.SCOPE_BASE'
            elif scope == ldap.SCOPE_ONELEVEL:
                scope_str = 'ldap.SCOPE_ONELEVEL'
            if host is not self.get_ldap_host() and host is not self.get_directory_host():
                raise Exception("Invalid host, must use either ldap host or directory host")
            log.debug("running paged search")
            log.debug("host: "+host)
            log.debug("who: "+who)
            log.debug("base: "+search_base)
            log.debug("filter: "+search_filter)
            log.debug("attrs: "+str(attrs))
            log.debug('scope: '+scope_str)
            log.debug("page size: "+str(page_size))
            try:
                conn = ldap.initialize(host)
                ldap.set_option( ldap.OPT_X_TLS_DEMAND, True )
                #ldap.set_option( ldap.OPT_DEBUG_LEVEL, 255 )
                ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT,ldap.OPT_X_TLS_NEVER)
                lc = SimplePagedResultsControl( ldap.LDAP_CONTROL_PAGE_OID, True, (page_size,''))
                if host is self.get_ldap_host():
                    result = conn.simple_bind_s(who,cred)
                else:
                    result = conn.simple_bind_s()
                result = []
                msgid = conn.search_ext(search_base, scope,  search_filter, attrs, serverctrls=[lc])
                pages = 0
                while True:
                    pages = pages + 1
                    log.debug("getting page "+str(pages))
                    rtype, rdata, rmsgid, serverctrls = conn.result3(msgid)
                    log.debug("result count: "+str(len(rdata)))
                    result.extend(rdata)
                    pctrls = [c for c in serverctrls if c.controlType == ldap.LDAP_CONTROL_PAGE_OID ]
                    if pctrls:
                        est, cookie = pctrls[0].controlValue
                        if cookie:
                            lc.controlValue = (page_size, cookie)
                            msgid = conn.search_ext(search_base, scope, search_filter, attrs, serverctrls=[lc])
                        else:
                            break
                    else:
                        log.warning("Warning:  Server ignores RFC 2696 control.")
                        break
                conn.unbind()
                return result
            except ldap.LDAPError, e:
                import traceback
                log.error("run_paged_search error:")
                log.error(traceback.format_exc())
                log.error(str(e))
                try:
                    conn.unbind()
                except:
                    pass
                return []

    __instance = None
    
    def __init__(self):
        if LDAPRunner.__instance is None:
            try:
                host = config['ldap_host']
                directory_host = config['ldap_directory_host']
                who = config['ldap_who']
                cred = config['ldap_cred']
            except KeyError, e:
                raise Exception("Must specify LDAP connection information in configuration file: "+str(e))
            LDAPRunner.__instance = LDAPRunner.__impl(host, directory_host, who, cred)
        self.__dict__['_Singleton__instance'] = LDAPRunner.__instance
    
    def __getattr__(self, attr):
        return getattr(self.__instance, attr)
    
    def __setattr__(self, attr, value):
        return setattr(self.__instance, attr, value)


def populate_student_from_active_directory(student):
    if student is None or (not isinstance(student, Student) and not type(student) == list):
        return
    
    search_base = "OU=Campus Accounts,DC=ad,DC=uiuc,DC=edu"
    attrs = ['displayName', 'givenName', 'sn', 'uiucEduStudentLevelName', 'uiucEduStudentProgramName', 'extensionName', 'sAMAccountName', 'distinguishedName']
    result = []
    if isinstance(student, Student):
        netid = student.netid
        search_filter = "(CN="+netid+")"
        result = LDAPRunner().run_search(search_base, search_filter, attrs)
    elif type(student) == list:
        search_filter = LDAPRunner().orFilter(map(lambda u:  "cn="+u.netid,student))
        result = LDAPRunner().run_paged_search(search_base, search_filter, attrs)
    if len(result) == 0:
        return
    def update_user(tup):
        from mossweb.lib.helpers import get_object_or_404
        if len(tup) != 2:
            return
        result_dict = tup[1]
        student = get_object_or_404(Student, netid=result_dict['sAMAccountName'].pop())
        try:
            student.levelName = result_dict['uiucEduStudentLevelName'].pop()
        except KeyError:
            if student.levelName is None or len(student.levelName) == 0:
                student.levelName = ""
        try:
            student.dn = result_dict['distinguishedName'].pop()
        except KeyError:
            if student.dn is None or len(student.dn) == 0:
                student.dn = ""
        try:
            student.givenName = result_dict['givenName'].pop()
        except KeyError:
            if student.givenName is None or len(student.givenName) == 0:
                student.givenName = ""
        try:
            student.displayName = result_dict['displayName'].pop()
        except KeyError:
            if student.displayName is None or len(student.displayName) == 0:
                student.displayName = ""
        try:
            student.surName = result_dict['sn'].pop()
        except KeyError:
            if student.surName is None or len(student.surName) == 0:
                student.surName = ""
        try:
            student.programName = result_dict['uiucEduStudentProgramName'].pop()
        except KeyError:
            if student.programName is None or len(student.programName) == 0:
                student.programName = ""
        try:
            extensions = result_dict['extensionName']
            regex = re.compile('Left_uiuc: (.*)', re.DOTALL)
            extensions = filter(lambda s: regex.match(s), extensions)
            if len(extensions) == 1:
                left_uiuc = extensions.pop()
                left_uiuc = regex.search(left_uiuc).group(1)
                student.leftUIUC = left_uiuc
            else:
                student.leftUIUC = "currently enrolled"
        except Exception, e:
            if student.leftUIUC is None or len(student.leftUIUC) == 0:
                student.leftUIUC = ""
            log.debug(str(e))
            print str(e)
        Session.commit()
    for tup in result:
        update_user(tup)
    
def populate_user_from_active_directory(user):
    if user is None or (not isinstance(user, User) and not type(user) == list):
        return
    search_base = "OU=Campus Accounts,DC=ad,DC=uiuc,DC=edu"
    attrs = ['givenName', 'sn', 'sAMAccountName', 'distinguishedName']
    result = []
    if isinstance(user, User):
        netid = user.name
        search_filter = "(CN="+netid+")"
        result = LDAPRunner().run_search(search_base, search_filter, attrs)
    elif type(user) == list:
        search_filter = LDAPRunner().orFilter(map(lambda u:  "cn="+u.name,user))
        result = LDAPRunner().run_paged_search(search_base, search_filter, attrs)
    def populate_user(tup):
        from mossweb.lib.helpers import get_object_or_404
        cn = tup[0]
        result_dict = tup[1]
        user = get_object_or_404(User, name=result_dict['sAMAccountName'].pop())
        try:
            user.givenName = result_dict['givenName'].pop()
        except KeyError:
            user.givenName = ""
        try:
            user.surName = result_dict['sn'].pop()
        except KeyError:
            user.surName = ""
        try:
            user.dn = result_dict['distinguishedName'].pop()
        except KeyError:
            user.dn = ""
        Session.commit()
    for tup in result:
        populate_user(tup)

def get_offering_dns(course):
    if course is None or not isinstance(course, Course):
        return []
    name = course.name
    search_base = "OU=Sections,OU=Class Rosters,DC=ad,DC=uiuc,DC=edu"
    search_filter = "(CN="+name+"*)"
    attrs = ['dn']
    result = LDAPRunner().run_search(search_base, search_filter, attrs)
    dns = []
    for tup in result:
        dns.append(tup[0])
    return dns

def get_student_dns_for_offering(offering):
    if len(offering.dns) == 0:
        return []
    search_base = "OU=Sections,OU=Class Rosters,DC=ad,DC=uiuc,DC=edu"
    attrs = ['member']
    search_filter = LDAPRunner().orFilter(map(lambda cn: cn[:cn.find(',')], offering.dns))
    student_cns = []
    result = LDAPRunner().run_paged_search(search_base, search_filter, attrs)
    import pprint
    if len(result) == 0:
        log.error("got bad return result from ldap query:")
        log.error(pprint.pformat(result))
        return []
    for (cn2, members_dict) in result:
        if members_dict.has_key('member'):
            members_list = members_dict['member']
            for student_cn in members_list:
                if student_cn not in student_cns:
                    student_cns.append(student_cn)
        else:
            log.error("Course "+cn2+" had no members, might want to check that out")
    return student_cns

def get_students_for_dns(dns):
    if len(dns) == 0:
        return []
    search_base = "OU=Campus Accounts,DC=ad,DC=uiuc,DC=edu"
    search_filter = LDAPRunner().orFilter(map(lambda cn: cn[:cn.find(',')], dns))
    attrs = ['sAMAccountName']
    result = LDAPRunner().run_paged_search(search_base, search_filter,attrs)
    netids = []
    for (cn, cn_dict) in result:
        if cn_dict.has_key('sAMAccountName'):
            lst = cn_dict['sAMAccountName']
            if len(lst) > 0:
                netid = lst[0]
                if netid not in netids:
                    netids.append(netid)
    found_students = Student.query.filter(Student.netid.in_(netids)).all()
    for student in found_students:
        netids.remove(student.netid)
    for new_student in netids:
        student = Student(netid=new_student)
        found_students.append(student)
    populate_student_from_active_directory(found_students)
    return found_students

def get_offering_info(offering_dns):
    if len(offering_dns) == 0:
        return []
    search_base = "OU=Sections,OU=Class Rosters,DC=ad,DC=uiuc,DC=edu"
    attrs = None
    search_filter = LDAPRunner().orFilter(map(lambda dn: dn[:dn.find(',')], offering_dns))
    result = LDAPRunner().run_search(search_base, search_filter, attrs)
    return result

def set_student_dns():
    netids = Session.query(Student.netid).all()

    search_base = "OU=Campus Accounts,DC=ad,DC=uiuc,DC=edu"
    search_filter = LDAPRunner().orFilter(map(lambda tup: "cn="+str(tup[0]), netids))
    attrs = ['sAMAccountName', 'distinguishedName']
    result = LDAPRunner().run_paged_search(search_base, search_filter, attrs)
    for (c, d) in result:
        cn = None
        if d.has_key("distinguishedName"):
            cn = d['distinguishedName'][0]
        netid = None
        if d.has_key('sAMAccountName'):
            netid = d['sAMAccountName'][0]
        if cn is not None and netid is not None:
            student = Student.query.filter_by(netid=netid).first()
            student.dn = cn
            Session.commit()
                
def set_user_dns():
    netids = Session.query(User.name).all()
    
    search_base = "OU=Campus Accounts,DC=ad,DC=uiuc,DC=edu"
    search_filter = LDAPRunner().orFilter(map(lambda tup: "cn="+str(tup[0]), netids))
    log.debug(search_filter)
    attrs = ['sAMAccountName', 'distinguishedName']
    result = LDAPRunner().run_search(search_base, search_filter, attrs)
    for (c, d) in result:
        cn = None
        if d.has_key("distinguishedName"):
            dn = d['distinguishedName'][0]
        netid = None
        if d.has_key('sAMAccountName'):
            netid = d['sAMAccountName'][0]
        if cn is not None and netid is not None:
            user = User.query.filter_by(name=netid).first()
            user.dn = cn
            Session.commit()
            
def set_course_dns():
    courses = Course.query.all()
    
    search_base = "OU=Courses,OU=Class Rosters,DC=ad,DC=uiuc,DC=edu"
    attrs = ["distinguishedName"]
    for course in courses:
        search_filter = "(cn="+course.name+" Current)"
        result = LDAPRunner().run_search(search_base, search_filter, attrs)
        for (c, d) in result:
            dn = None
            if d.has_key("distinguishedName"):
                dn = d['distinguishedName'][0]
            if dn is not None:
                course.dn = dn
                Session.commit()

def get_course_info(dn):
    search_base = "OU=Courses,OU=Class Rosters,DC=ad,DC=uiuc,DC=edu"
    attrs = None
    search_filter = "("+dn[:dn.find(',')]+")"
    return LDAPRunner().run_search(search_base, search_filter, attrs)

def get_all_courses():
    retval = {}
    search_base = "OU=Courses,OU=Class Rosters,DC=ad,DC=uiuc,DC=edu"
    attrs = ["name"]
    search_filter = "(cn=*)"
    result = LDAPRunner().run_paged_search(search_base, search_filter, attrs)
    
    for (cn, d) in result:
        if not d.has_key('name'):
            continue
        course_name = d['name'][0]
        department = course_name[:course_name.find(" ")]
        if not retval.has_key(department):
            retval[department] = []
        course_number = int(course_name[course_name.find(" ")+1:course_name.find(" Current")])
        if course_number not in retval[department]:
            retval[department].append(course_number)
    
    for key in retval.keys():
        retval[key].sort()
    return retval

def get_course_staff(course):
    if course is None or not isinstance(course, Course):
        return []
    if not course.name.startswith("CS "):
        return []
    regex = re.compile(r'(\S*)\s*(\d*).*')
    (department, course_number) = regex.match(course.name).group(1, 2)
    search_base = "OU=Class Staff,OU=CS,OU=Portal Groups,OU=Groups,OU=ECE,DC=ad,DC=uiuc,DC=edu"
    search_filter = "(CN="+department+" Staff "+course_number+")"
    attrs = ['member']
    result = LDAPRunner().run_search(search_base, search_filter, attrs)
    log.debug(pprint.pformat(result))
    retval = []
    if len(result) == 1:
        user_dns = result[0][1]['member']
        log.debug(pprint.pformat(user_dns))
        retval = get_users_for_dns(user_dns, course.name)
    return retval

def get_users_for_dns(dns, requested_course=""):
    if len(dns) == 0:
        return []
    search_base = "OU=Campus Accounts,DC=ad,DC=uiuc,DC=edu"
    search_filter = LDAPRunner().orFilter(map(lambda dn: dn[:dn.find(',')], dns))
    attrs = ['sAMAccountName']
    result = LDAPRunner().run_paged_search(search_base, search_filter,attrs)
    netids = []
    for (cn, cn_dict) in result:
        if cn_dict.has_key('sAMAccountName'):
            lst = cn_dict['sAMAccountName']
            if len(lst) > 0:
                netid = lst[0]
                if netid not in netids:
                    netids.append(netid)
    found_users = User.query.filter(User.name.in_(netids)).all()
    for user in found_users:
        netids.remove(user.name)
    for new_user in netids:
        user = User(name=new_user, superuser=False, enabled=False, requested_courses=requested_course)
        found_users.append(user)
    populate_user_from_active_directory(found_users)
    Session.commit()
    return found_users

def __get_directory_info(netid):
    search_base = 'ou=people,DC=UIUC,DC=EDU'
    search_filter = '(uiucEduNetID='+netid+')'
    search_attrs = None
    result = LDAPRunner().run_search(search_base,search_filter,search_attrs, host=LDAPRunner().get_directory_host())
    if len(result) is not 1:
        return {}
    data = result[0][1]
    return data

def get_student_directory_info(student):
    if student is None or not isinstance(student, Student):
        return {}
    return __get_directory_info(student.netid)

def get_user_directory_info(user):
    if user is None or not isinstance(user, User):
        return {}
    return __get_directory_info(user.name)

def user_test(netid):
    search_base = "OU=Campus Accounts,DC=ad,DC=uiuc,DC=edu"
    attrs = None
    result = []
    search_filter = "(CN="+netid+")"
    result = LDAPRunner().run_search(search_base, search_filter, attrs)
    from pprint import pprint
    pprint(result)    
    
    

def tester():
    course = Course.query.filter_by(name="CS 125").first()
    log.debug(pprint.pformat(get_course_staff(course)))
    
def directory_test():
    from pprint import pformat
    print pformat(__get_directory_info('cemeyer2'))
    