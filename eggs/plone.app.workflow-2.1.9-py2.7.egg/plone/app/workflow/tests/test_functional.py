#from zope.testing import doctest
from unittest import TestSuite
from utils import optionflags
from Testing.ZopeTestCase import FunctionalDocFileSuite
from base import WorkflowFunctionalTestCase


def test_suite():
    tests = ['onestateworkflow.txt', 'sharingpage.txt']
    suite = TestSuite()
    for test in tests:
        suite.addTest(FunctionalDocFileSuite(test,
            optionflags=optionflags,
            package="plone.app.workflow.tests",
            test_class=WorkflowFunctionalTestCase))
    return suite
