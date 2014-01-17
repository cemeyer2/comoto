from sqlalchemy import *
from migrate import *
from elixir import *
from mossweb.model import model

meta = MetaData()

def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.bind.echo = True
    setup_all()
    name_col = model.SubmissionFile.table.columns.get("name")
    name_col.alter(type=String(1024))

def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    setup_all()
    name_col = model.SubmissionFile.table.columns.get("name")
    name_col.alter(type=String(40))
