import unittest

from Testing.ZopeTestCase import FunctionalDocFileSuite as Suite
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.PloneTestCase import setupPloneSite

setupPloneSite()


def test_suite():
    suites = [
        Suite('assignment.txt',
              package='plone.app.contentrules.tests',
              test_class=ptc.FunctionalTestCase),
        Suite('simplepublish.txt',
              package='plone.app.contentrules.tests',
              test_class=ptc.FunctionalTestCase),
        Suite('multipublish.txt',
              package='plone.app.contentrules.tests',
              test_class=ptc.FunctionalTestCase)]

    return unittest.TestSuite(suites)
