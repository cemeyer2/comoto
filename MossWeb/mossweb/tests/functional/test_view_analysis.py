from mossweb.tests import *

class TestViewAnalysisController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='view_analysis', action='index'))
        # Test response...
