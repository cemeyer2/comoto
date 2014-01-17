from mossweb.tests import *

class TestHistoryController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='history', action='index'))
        # Test response...
