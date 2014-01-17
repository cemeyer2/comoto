from sqlalchemy import *
from migrate import *
from elixir import *
from mossweb.model import model
from sqlalchemy.exc import OperationalError
from mossweb.lib import ldap_helpers as lh

meta = MetaData()

def safe_create_col(col, model, engine):
    try:
        col.create(model.table, populate_default=False)
    except OperationalError, e:
        print "ERROR CREATING column---"+str(e)

def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.bind.echo = True
    setup_all()
    
    programNameCol = model.Student.table.columns.get("programName")
    levelNameCol = model.Student.table.columns.get("levelName")
    givenNameCol = model.Student.table.columns.get("givenName")
    surNameCol = model.Student.table.columns.get("surName")
    displayNameCol = model.Student.table.columns.get("displayName")
    givenNameCol2 = model.User.table.columns.get("givenName")
    surNameCol2 = model.User.table.columns.get("surName")

    safe_create_col(programNameCol, model.Student, migrate_engine)
    safe_create_col(levelNameCol, model.Student, migrate_engine)
    safe_create_col(givenNameCol, model.Student, migrate_engine)
    safe_create_col(surNameCol, model.Student, migrate_engine)
    safe_create_col(displayNameCol, model.Student, migrate_engine)
    safe_create_col(givenNameCol2, model.Student, migrate_engine)
    safe_create_col(surNameCol2, model.Student, migrate_engine)
    
    
    #this takes too long on maggie, so do it later, update in student
    #history view only for now
    #for student in model.Student.query.all():
    #    lh.populate_student_from_active_directory(student)
    for user in model.User.query.all():
        lh.populate_user_from_active_directory(user)

def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    setup_all()
    programNameCol = model.Student.table.columns.get("programName")
    levelNameCol = model.Student.table.columns.get("levelName")
    givenNameCol = model.Student.table.columns.get("givenName")
    surNameCol = model.Student.table.columns.get("surName")
    displayNameCol = model.Student.table.columns.get("displayName")
    #programNameCol.drop()
    #levelNameCol.drop()
    #givenNameCol.drop()
    #surNameCol.drop()
    #displayNameCol.drop()
