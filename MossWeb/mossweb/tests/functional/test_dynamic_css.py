from mossweb.tests import *

class TestDynamicCssController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='dynamic_css', action='index'))
        # Test response...
