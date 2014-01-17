from mossweb.tests import *

class TestOfferingController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='offering', action='index'))
        # Test response...
