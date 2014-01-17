from sqlalchemy import *
from migrate import *
from elixir import *
from mossweb import model
from mossweb.model.model import StudentSubmission, PartnerLink, ExtraData
from sqlalchemy.exc import OperationalError
import traceback
from pprint import pprint
from migrate.changeset.constraint import ForeignKeyConstraint
from mossweb.lib.partner_helpers import create_image_for_partnerlink

meta = MetaData()

def getTables(model_cls):
    tables = []
    for key in sorted(model.metadata.tables.keys()):
        if key.startswith(model_cls.table.name):
            tables.append(model.metadata.tables[key])
    return tables

def createExistingPartnerLinks():
    try:
        submissions = StudentSubmission.query.all()
        for submission in submissions:
            for partner in submission.partners:
                partner_submission = StudentSubmission.query.filter(StudentSubmission.student == partner).filter(StudentSubmission.fileset==submission.fileset).first()
                pl = PartnerLink()
                pl.submission1 = [submission]
                pl.submission2 = [partner_submission]
                pl.type = "direct"
                pl.linkage.append(submission)
                pl.linkage.append(partner_submission)
                model.Session.commit()
                pl.images = [create_image_for_partnerlink(pl)]
                model.Session.commit()
    except:
        print traceback.format_exc()

def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.bind.echo = True
    setup_all()
    for table in getTables(PartnerLink):
        try:
            table.create()
        except:
            pass
    #create studentsubmission->manytomany->partnerlink relationship
    try:
        model.metadata.tables['studentsubmission_partnerLinks__submission'].create()
    except:
        pass
    #create extradata link
    try:
        col = ExtraData.table.columns.get('partnerLink_id')
        col.create(ExtraData.table, "ix_extradata_partnerLink_id", populate_default=False)
    except Exception, e:
        print str(e)
        print traceback.format_exc()
    createExistingPartnerLinks()

#doesnt work, mysql crappy errors with foreign key constraints
def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.bind.echo = True
    setup_all()
    try:
#        constraints = ExtraData.table.constraints
#        for c in constraints:
#            if 'partnerLink_id' in c.columns:
        fkc = ForeignKeyConstraint([ExtraData.table.c.partnerLink_id], [PartnerLink.table.c.id])
        fkc.drop()        
        indexes = ExtraData.table.indexes
        for l in indexes:
            if l.name == "ix_extradata_partnerLink_id":
                l.drop()
    except:
        print traceback.format_exc()
    try:
        col = ExtraData.table.columns.get('partnerLink_id')
        col.drop(ExtraData.table)
    except Exception, e:
        print str(e)
        print traceback.format_exc()
    tables = getTables(PartnerLink)
    tables.reverse()
    for table in tables:
        table.drop()
    try:
        model.metadata.tables['studentsubmission_partnerLinks__submission'].drop()
    except:
        pass