from mossweb.tests import *

class TestCourseController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='course', action='index'))
        # Test response...
