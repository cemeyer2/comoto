'''
Created on Apr 1, 2011

@author: chuck
'''

from mossweb.model.model import PartnerLink
import pygraphviz
from mossweb.model import model
from PIL import Image
import os

def create_image_for_partnerlink(link):
    
    def __studentsubmission_to_string(sub):
        netid = sub.student.netid
        offering = sub.offering
        course = offering.course
        semester = offering.semester
        return str(netid) + " " + str(course.name) + " " + str(semester.season) + " "+ str(semester.year)
    
    linkage = link.linkage
    img = model.Image()
    img.name = "Partners Linkage"
    img.title = "Partners Linkage"
    img.type = "PNG"
    img.filename = "partners.png"
    img.owner_type = "PartnerLink"
    img.owner_id = link.id
    graph = pygraphviz.AGraph()
    
    graph.graph_attr['label'] = "Partner linkage between "+__studentsubmission_to_string(link.submission1[0]) + " and " + __studentsubmission_to_string(link.submission2[0])
    graph.graph_attr['overlap'] = 'scale' # false
    graph.graph_attr['splines'] = 'true'
    graph.graph_attr['overlap'] ="prism"
    
    for submission in linkage:
        graph.add_node(__studentsubmission_to_string(submission))
    for index in range(len(linkage)-1):
        sub1 = linkage[index]
        sub2 = linkage[index+1]
        graph.add_edge(__studentsubmission_to_string(sub1), __studentsubmission_to_string(sub2), label="",dirType="none",color="black")
    graph.layout(prog="neato")
    graph.draw("/tmp/graph.png", args='-Tpng:gd:gd ')
    image = Image.open('/tmp/graph.png')
    image.thumbnail((150,150), Image.ANTIALIAS)
    image.save('/tmp/graph-thumbnail.png')
    image2 = Image.open('/tmp/graph.png')
    width,height = image2.size
    image2.thumbnail((int(width*.3),int(height*.3)), Image.ANTIALIAS)
    image2.save('/tmp/graph-medium.png')
    try:
        f = open('/tmp/graph.png', 'r')
        data = f.read()
        img.imageData = data
        f.close()
        f2 = open('/tmp/graph-thumbnail.png')
        data2 = f2.read()
        f2.close()
        img.thumbnailData = data2
        f3 = open('/tmp/graph-medium.png')
        data3 = f3.read()
        f3.close()
        img.mediumData = data3                
    except Exception, e:
        pass
    try:               
        os.remove('/tmp/graph.png')
    except Exception, e:
        pass
    try:
        os.remove('/tmp/graph-thumbnail.png')
    except Exception, e:
        pass
    try:
        os.remove('/tmp/graph-medium.png')
    except Exception, e:
        pass
    return img
        