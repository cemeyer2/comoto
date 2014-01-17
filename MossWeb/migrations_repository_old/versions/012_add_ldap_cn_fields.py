from sqlalchemy import *
from migrate import *
from elixir import *
from mossweb.model import model
from sqlalchemy.exc import OperationalError
from mossweb.lib import ldap_helpers as lh

meta = MetaData()

def safe_create_col(col, model, engine, populate_default=False):
    try:
        col.create(model.table, populate_default=populate_default)
    except OperationalError, e:
        print "ERROR CREATING column---"+str(e)

def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.bind.echo = True
    setup_all()
    
    studentCNCol = model.Student.table.columns.get("cn")
    offeringCNCol = model.Offering.table.columns.get("cns", True)
    userCNCol = model.User.table.columns.get("cn")
    courseCNCol = model.Course.table.columns.get("cn")

    safe_create_col(studentCNCol, model.Student, migrate_engine)
    safe_create_col(offeringCNCol, model.Offering, migrate_engine)
    safe_create_col(userCNCol, model.User, migrate_engine)
    safe_create_col(courseCNCol, model.Course, migrate_engine)
    
    for offering in model.Offering.query.all():
        offering.cns = []
        
    lh.set_student_cns()
    lh.set_user_cns()
    lh.set_course_cns()
    
    model.Session.commit()

def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    setup_all()
    studentCNCol = model.Student.table.columns.get("cn")
    offeringCNCol = model.Offering.table.columns.get("cns", True)
    userCNCol = model.User.table.columns.get("cn")
    courseCNCol = model.Course.table.columns.get("cn")
    
    studentCNCol.drop()
    offeringCNCol.drop()
    userCNCol.drop()
    courseCNCol.drop()