from paste.deploy import loadapp
import matplotlib.pyplot as plt
from mossweb import model as model
from mossweb.model.model import * 
from mossweb.lib import helpers as h

def run(filename):
    "Write your commands here."    
    app = loadapp('config:' + filename)

    
    assignment = h.get_object_or_404(Assignment, id=1)
    ma = assignment.analysis.mossAnalysis
    matches = ma.matches
    l = []
    for match in matches:
        l.append(match.get_score())
    plt.hist(l, 100)
    plt.ylabel('number of matches')
    plt.xlabel('match score')
    plt.savefig('/tmp/histogram.png', transparent=True)
    
    
