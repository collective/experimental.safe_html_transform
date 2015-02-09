import doctest
import unittest

from Testing import ZopeTestCase as ztc

from archetypes.querywidget.tests import base


def test_suite():
    # Wire in integration.txt tests as doctests in the integration layer
    return unittest.TestSuite([
        ztc.ZopeDocFileSuite(
            'tests/integration.rst', package='archetypes.querywidget',
            test_class=base.ArchetypesQueryWidgetTestCase,
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS),
    ])
