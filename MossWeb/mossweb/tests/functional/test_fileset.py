from mossweb.tests import *

class TestFilesetController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='fileset', action='index'))
        # Test response...
