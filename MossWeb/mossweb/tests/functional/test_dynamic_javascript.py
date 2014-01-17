from mossweb.tests import *

class TestDynamicJavascriptController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='dynamic_javascript', action='index'))
        # Test response...
