from mossweb.tests import *

class TestMossController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='moss', action='index'))
        # Test response...
