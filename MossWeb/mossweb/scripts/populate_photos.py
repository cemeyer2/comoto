from paste.deploy import loadapp

def run(filename):
    "Write your commands here."    
    app = loadapp('config:' + filename)
    from mossweb import model as model
    from mossweb.model.model import Student 
    from mossweb.lib import helpers as h
    for student in Student.query.all():
        if student.netid is not None:
            print "populating "+str(student.netid)
            h.get_icard_photo(student)
            model.Session.commit()
    model.Session.commit()
