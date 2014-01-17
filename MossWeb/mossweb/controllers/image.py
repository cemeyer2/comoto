import logging

from pylons import request, response, session, tmpl_context as c
from pylons.controllers.util import abort, redirect_to

from mossweb.lib.base import BaseController, render
from mossweb.model.model import Image, Student
import mimetypes
from mossweb.lib import helpers as h
from mossweb.lib.access import check_image_access, check_student_access
import urllib2, os
from mossweb.model import Session


log = logging.getLogger(__name__)

class ImageController(BaseController):

    def view(self, id):
        image_id = int(id.split(".")[0]) #calls will be like /image/view/1.png
        image = h.get_object_or_404(Image, id=image_id)
        check_image_access(image)
        type = mimetypes.guess_type(image.filename)[0]
        if type is None:
            if image.filename.endswith("png"):
                type = 'image/png'
            #add others as necessary
        response.content_type = type
        response.content_length = len(image.imageData)
        return image.imageData 
    
    def icard(self, id):
        student = h.get_object_or_404(Student, netid=id)
        check_student_access(student)
        response.content_type = "image/jpeg"
        return h.get_icard_photo(student)
        
