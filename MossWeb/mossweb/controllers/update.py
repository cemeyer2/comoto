import logging
from mossweb.controllers.api import ApiController
from mossweb.lib.decorators import require_enabled_user
from pylons import request, response, session, tmpl_context as c
from mossweb.lib import helpers as h
from mossweb.model.model import Assignment
from mossweb.lib.base import BaseController, render
from pylons.decorators import jsonify
from mossweb.lib.decorators import require_superuser
import os
import subprocess, time

log = logging.getLogger(__name__)

class UpdateController(BaseController):

    @require_superuser()
    def update(self):
        user = h.get_user(request.environ)
        #hg parents --template="r{rev} {date|date} by {author}\n"
        args = ['bash', '/mounts/comoto/disks/0/pylons/comoto1.5/update_comoto.sh', '&']
        hg_process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=os.path.dirname(__file__))
        time.sleep(15)
        return "Update Successful"
        