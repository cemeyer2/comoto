from mossweb.tests import *

class TestUserTestController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='user_test', action='index'))
        # Test response...
