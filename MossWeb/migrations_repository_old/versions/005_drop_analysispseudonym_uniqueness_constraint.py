from sqlalchemy import *
from migrate import *

from sqlalchemy import *
from sqlalchemy.exc import OperationalError
from migrate import *
from elixir import *
from mossweb.model import model, Session
from migrate.changeset import *
from migrate.changeset.exceptions import *

meta = MetaData()

#using_table_options(UniqueConstraint('analysis_id', 'pseudonym'))

def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.bind.echo = True
    setup_all()
    table = model.AnalysisPseudonym.table
    analysis_id_col = table.columns.get("analysis_id")
    pseudonym_col = table.columns.get("pseudonym")
    u = UniqueConstraint(analysis_id_col, pseudonym_col)
    try:
        u.drop(cascade=False)
    except NotSupportedError, e:
        print "FAILED TO DROP CONSTRAINT: "+str(e)
    except OperationalError, e:
        print "FAILED TO DROP CONSTRAINT: "+str(e)
        try:
            sql = "ALTER TABLE analysispseudonym DROP INDEX analysis_id;"
            migrate_engine.execute(sql)
        except OperationalError, e:
            pass

def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    setup_all()
    