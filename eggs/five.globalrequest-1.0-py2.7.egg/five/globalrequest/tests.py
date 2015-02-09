import unittest

class TestHooks(unittest.TestCase):
    
    def test_set(self):
        
        class FauxRequest(object):
            pass
        
        class FauxEvent(object):
            request = FauxRequest()
        
        event = FauxEvent()
        
        from five.globalrequest.hooks import set_
        set_(event)
        
        from zope.globalrequest import getRequest
        self.assertEquals(getRequest(), event.request)
    
    def test_clear(self):
        
        class FauxRequest(object):
            pass
        
        class FauxEvent(object):
            request = FauxRequest()
        
        event = FauxEvent()
        
        from zope.globalrequest import setRequest
        setRequest(event.request)
        
        from five.globalrequest.hooks import clear
        clear(event)
        
        from zope.globalrequest import getRequest
        self.assertEquals(getRequest(), None)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)