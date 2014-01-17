from sqlalchemy import *
from migrate import *

from sqlalchemy import *
from migrate import *
from elixir import *
from mossweb.model import model
from sqlalchemy.exc import OperationalError

meta = MetaData()

def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.bind.echo = True
    setup_all()
    pruned_col = model.MossAnalysis.table.columns.get("pruned_offering_id")
    try:
        pruned_col.create(model.MossAnalysis.table)
    except OperationalError, e:
        print "FAILED TO ADD COLUMN: "+str(e)    

def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    setup_all()
    pruned_col = model.MossAnalysis.table.columns.get("pruned_offering_id")
    #pruned_col.drop()