from mossweb.tests import *

class TestSemesterController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='semester', action='index'))
        # Test response...
