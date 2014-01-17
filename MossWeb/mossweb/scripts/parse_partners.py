from paste.deploy import loadapp
from paste.script.util.logging_config import fileConfig

def run(filename):
    app = loadapp('config:' + filename)
    from mossweb import model as model
    from mossweb.model.model import StudentSubmission 
    from mossweb.lib import helpers as h
    for submission in StudentSubmission.query.all():
        h.parse_partners(submission)
    model.Session.commit()
