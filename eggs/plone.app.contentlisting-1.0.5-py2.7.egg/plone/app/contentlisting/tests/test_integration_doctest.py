import doctest
import unittest

from Testing import ZopeTestCase as ztc

from .base import ContentlistingFunctionalTestCase


def test_suite():
    return unittest.TestSuite([
        ztc.ZopeDocFileSuite(
            'tests/integration.txt', package='plone.app.contentlisting',
            test_class=ContentlistingFunctionalTestCase,
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS),
        ])
