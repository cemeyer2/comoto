from mossweb.tests import *

class TestCssController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='css', action='index'))
        # Test response...
