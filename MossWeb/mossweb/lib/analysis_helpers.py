'''
Created on Mar 30, 2010

@author: chuck
'''

from mossweb.model.model import *
from mossweb.model import Session
import logging
from pylons import config

log = logging.getLogger(__name__)

from mossweb.lib.moss_helpers import *

import os, tempfile, random, shutil, subprocess

from pylons.controllers.util import abort
from mossweb.lib import helpers as h



def prune_moss_analysis(mossAnalysis, offering):
    if not isinstance(mossAnalysis, MossAnalysis):
        log.warning("arg mossAnalysis not of type MossAnalysis, is of type "+str(type(mossAnalysis)))
        abort(500)
    if not isinstance(offering, Offering):
        log.warning("arg offering not of type Offering, is of type "+str(type(offering)))
        abort(500)
    def _should_hide(match):
        should_delete = True
        if match.submission1.fileset.offering == offering:
            should_delete = False
        elif match.submission2.fileset.offering == offering:
            should_delete = False
        return should_delete
    
    for match in mossAnalysis.matches:
        match.hidden = _should_hide(match)

    mossAnalysis.pruned = True
    mossAnalysis.prunedOffering = offering
    Session.commit()

def get_offerings_for_analysis(analysis):
    if not isinstance(analysis, Analysis):
        log.warning("arg analysis not of type Analysis, is of type "+str(type(analysis)))
        abort(500)
    offerings = []
    for fileset in analysis.assignment.filesets:
        if fileset.offering not in offerings:
            offerings.append(fileset.offering)
    return filter(lambda offering: offering.semester.row_type=='semester',offerings)