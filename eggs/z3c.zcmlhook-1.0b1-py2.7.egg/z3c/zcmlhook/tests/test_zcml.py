from unittest import TestCase

from zope.configuration import xmlconfig
from zope.configuration.config import ConfigurationConflictError

import zope.component.testing
import z3c.zcmlhook

import threading

testState = threading.local()

def test_fn1():
    testState.executions.append('test_fn1')

def test_fn2():
    testState.executions.append('test_fn2')

class TestZCMLDeclarations(TestCase):
    
    def setUp(self):
        global testState
        testState.executions = []
    
    def tearDown(self):
        zope.component.testing.tearDown()

    def test_invoke(self):
        zcml = xmlconfig.XMLConfig("test1.zcml", z3c.zcmlhook.tests)
        zcml()
        
        self.assertEquals(['test_fn1'], testState.executions)
    
    def test_invoke_order(self):
        zcml = xmlconfig.XMLConfig("test2.zcml", z3c.zcmlhook.tests)
        zcml()
        
        self.assertEquals(['test_fn2', 'test_fn1'], testState.executions)
    
    def test_invoke_conflict(self):
        zcml = xmlconfig.XMLConfig("test3.zcml", z3c.zcmlhook.tests)
        self.assertRaises(ConfigurationConflictError, zcml)
    
    def test_custom_discriminator(self):
        zcml = xmlconfig.XMLConfig("test4.zcml", z3c.zcmlhook.tests)
        zcml()
        self.assertEquals(['test_fn1', 'test_fn1'], testState.executions)
    
def test_suite():
    import unittest
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
