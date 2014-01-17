from sqlalchemy import *
from migrate import *
from elixir import *
from mossweb.model import model, Session
from sqlalchemy.exc import OperationalError

meta = MetaData()

def safe_create_table(model):
    try:
        model.table.create()
    except OperationalError, e:
        "ERROR CREATING TABLE---"+str(e)

def safe_create_col(col, model, engine):
    try:
        col.create(model.table, populate_default=False)
    except OperationalError, e:
        print "ERROR CREATING column---"+str(e)

    
def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.bind.echo = True
    setup_all()
    safe_create_table(model.StaticMossGraph)


def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    model.StaticMossGraph.table.drop()
    staticMossGraphsCol = model.Assignment.table.columns.get("staticMossGraphs")
    staticMossGraphsCol.drop()
    setup_all()
    