import unittest
import doctest

from Products.Five import zcml
from Products.Five import fiveconfigure

from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
from Testing import ZopeTestCase as ztc

import plone.browserlayer
import plone.browserlayer.tests

ptc.setupPloneSite()


class PloneBrowserLayerLayer(PloneSite):

    @classmethod
    def setUp(cls):
        fiveconfigure.debug_mode = True
        zcml.load_config('tests/testing.zcml', plone.browserlayer)
        zcml.load_config('configure.zcml', plone.browserlayer)
        fiveconfigure.debug_mode = False
        ztc.installPackage('plone.browserlayer')

    @classmethod
    def tearDown(cls):
        pass


class PloneBrowserLayerTestCase(ptc.FunctionalTestCase):
    layer = PloneBrowserLayerLayer


def test_suite():
    return unittest.TestSuite([

        # Demonstrate the main content types
        ztc.ZopeDocFileSuite(
            'README.txt', package='plone.browserlayer',
            test_class=PloneBrowserLayerTestCase,
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE | doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS),

        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
