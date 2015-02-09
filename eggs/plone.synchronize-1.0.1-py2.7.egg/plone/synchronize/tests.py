import unittest

from threading import Lock
from plone.synchronize import synchronized

class StupidStack(object):

    _elements = [] # not thread safe
    _lock = Lock()
    
    @synchronized(_lock)
    def push(self, item):
        self._elements.append(item)
    
    @synchronized(_lock)
    def pop(self):
        last = self._elements[-1]
        del self._elements[-1]
        return last

_global_lock = Lock()
_global_list = []

@synchronized(_global_lock)
def reverse_global_list():
    global _global_list
    _global_list.reverse()

class Test(unittest.TestCase):
    
    def test_instance_method(self):
        
        shared_stack = StupidStack()
        shared_stack.push("one")
        item = shared_stack.pop()
        
        self.assertEquals("one", item)
        
        # raises exception
        
        raised = False
        try:
            shared_stack.pop()
        except IndexError:
            raised = True
        
        self.failUnless(raised)
        
        # should not be dead-locked even after an exception
        
        shared_stack.push("two")
        item = shared_stack.pop()
        
        self.assertEquals("two", item)
        
    def test_function(self):
        global _global_list
        _global_list.extend([1,2,3])
        
        reverse_global_list()
        reverse_global_list()
        reverse_global_list()
        
        self.assertEquals([3,2,1], _global_list)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
