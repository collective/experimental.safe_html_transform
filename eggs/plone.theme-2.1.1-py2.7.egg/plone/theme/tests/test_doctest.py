import unittest
import doctest

from zope.interface import Interface

from Products.Five import zcml
from Products.Five import fiveconfigure

from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
from Testing import ZopeTestCase as ztc

import plone.theme
import plone.theme.tests

ptc.setupPloneSite()


class PloneThemeLayer(PloneSite):

    @classmethod
    def setUp(cls):
        fiveconfigure.debug_mode = True
        zcml.load_config('configure.zcml', plone.theme)
        zcml.load_config('tests.zcml', plone.theme.tests)
        fiveconfigure.debug_mode = False

    @classmethod
    def tearDown(cls):
        pass


class PloneThemeTestCase(ptc.FunctionalTestCase):
    layer = PloneThemeLayer


def test_suite():
    return unittest.TestSuite([

        # Demonstrate the main content types
        ztc.ZopeDocFileSuite(
            'README.txt', package='plone.theme',
            test_class=PloneThemeTestCase,
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE | doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS),

        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
