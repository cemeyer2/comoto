from paste.deploy import loadapp

def run(filename):
    "Write your commands here."    
    app = loadapp('config:' + filename)
    from mossweb import model as model
    model.metadata.bind.echo = True
    from mossweb.model.model import FileSet, Analysis 
    from mossweb.lib import ldap_helpers as lh
    import shutil
    for fileset in FileSet.query.filter(FileSet.isComplete == False).all():
        try:
            shutil.rmtree(fileset.tempDir)
        except:
            pass
        fileset.delete()
    for analysis in Analysis.query.filter(Analysis.complete == False).all():
        analysis.filesets = []
        try:
            shutil.rmtree(analysis.workDirectory)
        except:
            pass
        try:
            shutil.rmtree(analysis.webDirectory)
        except:
            pass
        analysis.delete()
    model.Session.commit()
