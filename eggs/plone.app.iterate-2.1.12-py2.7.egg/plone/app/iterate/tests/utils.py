#

from Products.Archetypes.ReferenceEngine import Reference
from Products.PloneTestCase import five
class CustomReference( Reference ): pass
        
class IterateLayer:

    def setUp(cls):
        '''Sets up the CA by loading etc/site.zcml.'''
        five.safe_load_site()
    setUp = classmethod(setUp)

    def tearDown(cls):
        '''Cleans up the CA.'''
        five.cleanUp()
    tearDown = classmethod(tearDown)
