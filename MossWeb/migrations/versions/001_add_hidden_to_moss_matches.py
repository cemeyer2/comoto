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
    hidden_col = model.MossMatch.table.columns.get("hidden")
    try:
        hidden_col.create(model.MossAnalysis.table, populate_default=False)
        matches = model.MossMatch.query.all()
        for match in matches:
            match.hidden = False
        model.Session.commit()
    except OperationalError, e:
        print "FAILED TO ADD COLUMN: "+str(e)    

def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    setup_all()
    hidden_col = model.MossMatch.table.columns.get("hidden")
    hidden_col.drop()