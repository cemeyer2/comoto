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
    
    leftUIUCCol = model.Student.table.columns.get("leftUIUC")


    safe_create_col(leftUIUCCol, model.Student, migrate_engine)

    #for student in model.Student.query.all():
    #    lh.populate_student_from_active_directory(student)


def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.bind.echo = True
    setup_all()
    leftUIUCCol = model.Student.table.columns.get("leftUIUC")
    leftUIUCCol.drop()

