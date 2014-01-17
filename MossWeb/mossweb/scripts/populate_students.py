from paste.deploy import loadapp

def run(filename):
    "Write your commands here."    
    app = loadapp('config:' + filename)
    from mossweb import model as model
    from mossweb.model.model import Student 
    from mossweb.lib import ldap_helpers as lh
    for student in Student.query.all():
        if student.netid is not None:
            print "populating "+str(student.netid)
            lh.populate_student_from_active_directory(student)
    model.Session.commit()
