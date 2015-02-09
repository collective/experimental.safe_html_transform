import doctest
import unittest

from Products.PloneTestCase.layer import ZCMLLayer as BaseZCMLLayer

# BBB for Zope 2.12
try:
    from Zope2.App import zcml
except ImportError:
    from Products.Five import zcml


class ZCMLLayer(BaseZCMLLayer):

    @classmethod
    def testSetUp(cls):
        import plone.formwidget.autocomplete
        zcml.load_config('testing.zcml', plone.formwidget.autocomplete)

    @classmethod
    def testTearDown(cls):
        pass


def test_suite():
    readme_txt = doctest.DocFileSuite('README.txt')
    readme_txt.layer = ZCMLLayer
    return unittest.TestSuite([
        readme_txt,
        ])
