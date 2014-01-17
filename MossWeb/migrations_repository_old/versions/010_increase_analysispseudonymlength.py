from sqlalchemy import *
from migrate import *
from elixir import *
from mossweb.model import model, Session

meta = MetaData()

def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.bind.echo = True
    setup_all()
    col = model.AnalysisPseudonym.table.columns.get("pseudonym")
    col.alter(type=String(128))

def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    setup_all()
    col = model.AnalysisPseudonym.table.columns.get("pseudonym")
    col.alter(type=String(16))