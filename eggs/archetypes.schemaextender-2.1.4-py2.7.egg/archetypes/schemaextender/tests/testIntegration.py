import doctest
from unittest import TestSuite

from zope.component import testing
from Testing import ZopeTestCase as ztc

from archetypes.schemaextender.tests.base import TestCase


def test_suite():
    return TestSuite([

        doctest.DocTestSuite(
           module='archetypes.schemaextender.extender',
           setUp=testing.setUp, tearDown=testing.tearDown),

        ztc.FunctionalDocFileSuite(
            'usage.txt', package='archetypes.schemaextender',
            test_class=TestCase),

        ])
