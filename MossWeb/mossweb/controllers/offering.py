import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from mossweb.lib.base import BaseController, render

from mossweb.model.model import Offering, Session
from mossweb.lib.access import check_offering_access
from mossweb.lib.ldap_helpers import get_offering_dns, get_offering_info, get_student_dns_for_offering, get_students_for_dns
from mossweb.lib import helpers as h
from mossweb.lib.decorators import require_enabled_user

log = logging.getLogger(__name__)

class OfferingController(BaseController):
    
    @require_enabled_user()
    def __before__(self, controller, action):
        pass

    def manage(self, id):
        if id is None:
            abort(404)
        offering = h.get_object_or_404(Offering, id=id)
        check_offering_access(offering)
        potential_dns = get_offering_dns(offering.course)
        potential_dns = filter(lambda dn: str(offering.semester.year) in dn and offering.semester.season in dn, potential_dns)
        offering_info = get_offering_info(potential_dns)
        potential_offerings_dict = {}
        for (dn, d) in offering_info:
            potential_offerings_dict[dn] = d['name']
        c.potential_offerings_dict = potential_offerings_dict
        c.offering = offering
        offering_info = get_offering_info(offering.dns)
        offerings_dict = {}
        for (dn, d) in offering_info:
            offerings_dict[dn] = d['name']
            if c.potential_offerings_dict.has_key(dn):
                del c.potential_offerings_dict[dn]
        c.offerings_dict = offerings_dict
        return render("/derived/offering/manage.html")
    
    def link_dn(self, id):
        if id is None or (not request.params.has_key('dn') and not request.params.has_key("count")):
            abort(404)
        offering = h.get_object_or_404(Offering, id=id)
        check_offering_access(offering)
        if request.params.has_key("dn"):
            dn = request.params['dn']
            if dn not in offering.dns:
                offering.dns.append(dn)
        elif request.params.has_key("count"):
            dn_count = int(request.params['count'])
            for i in range(0,dn_count):
                dn = request.params['dn'+str(i)]
                if not dn in offering.dns:
                    offering.dns.append(dn)
        Session.commit()
        redirect_to(controller="offering", action="manage", id=offering.id)
        
    def unlink_dn(self, id):
        if id is None or not request.params.has_key('dn'):
            abort(404)
        offering = h.get_object_or_404(Offering, id=id)
        check_offering_access(offering)
        dn = request.params['dn']
        if dn in offering.dns:
            offering.dns.remove(dn)
        Session.commit()
        redirect_to(controller="offering", action="manage", id=offering.id)
        
    def view_roster(self, id):
        if id is None:
            abort(404)
        offering = h.get_object_or_404(Offering, id=id)
        check_offering_access(offering)
        student_dns = get_student_dns_for_offering(offering)
        c.students = get_students_for_dns(student_dns)
        for student in c.students:
            if offering not in student.offerings:
                student.offerings.append(offering)
        c.students.sort()
        c.offering = offering
        Session.commit()
        return render("/derived/offering/roster.html")