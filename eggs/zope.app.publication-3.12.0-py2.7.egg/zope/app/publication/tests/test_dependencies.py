import os
import unittest

from zope.app.publication.traversers import SimpleComponentTraverser
from zope.component import getMultiAdapter
from zope.component.testlayer import ZCMLFileLayer
from zope.interface import implements
from zope.publisher.browser import TestRequest
from zope.publisher.interfaces.browser import IBrowserPublisher

import zope.app.publication.tests


class ZCMLDependencies(unittest.TestCase):
    layer = ZCMLFileLayer(zope.app.publication.tests,
                          zcml_file='ftest_zcml_dependencies.zcml',
                          name='PublicationDependenciesLayer')

    def test_zcml_can_load_with_only_zope_component_meta(self):
        # this is just an example.  It is supposed to show that the
        # configure.zcml file has loaded successfully.

        request = TestRequest()

        sample = object()
        res = getMultiAdapter(
            (sample, request), IBrowserPublisher)
        self.failUnless(isinstance(res, SimpleComponentTraverser))
        self.failUnless(res.context is sample)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ZCMLDependencies))
    return suite

