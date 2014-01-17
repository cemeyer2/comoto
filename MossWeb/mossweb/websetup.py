# -*- coding: utf-8 -*-
"""Setup the MossWeb application"""
import logging

from mossweb.config.environment import load_environment

log = logging.getLogger(__name__)

from pylons import config
from elixir import *
from mossweb import model as model
from mossweb.model import Session
from mossweb.model.model import User, SolutionSemester, BaseSemester
from mossweb.lib.ldap_helpers import populate_user_from_active_directory

def setup_app(command, conf, vars):
    """Place any commands to setup mossweb here"""
    load_environment(conf.global_conf, conf.local_conf)
    model.metadata.create_all()

    # Initialisation here ... this sort of stuff:

    # some_entity = model.Session.query(model.<modelfile>.<Some_Entity>).get(1)
    # e.g. foo = model.Session.query(model.identity.User).get(1)
    # from datetime import datetime
    # some_entity.poked_on = datetime.now()
    # model.Session.add(some_entity)
    u = User(name="cemeyer2", superuser=True, enabled=True)
    populate_user_from_active_directory(u)
    s = SolutionSemester(year=-1, season=u"Fall", isSolution=True)
    s2 = BaseSemester(year=-2, season=u'Fall', isSolution=True)
    Session.commit()
