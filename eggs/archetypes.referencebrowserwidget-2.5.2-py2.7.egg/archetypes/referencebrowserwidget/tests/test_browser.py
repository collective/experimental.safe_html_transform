from unittest import TestSuite
import doctest
from Testing import ZopeTestCase as ztc
from archetypes.referencebrowserwidget.tests.base import FunctionalTestCase

optionflags = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


def test_suite():
    return TestSuite([
        ztc.FunctionalDocFileSuite('reference_access.txt',
            package='archetypes.referencebrowserwidget.tests',
            test_class=FunctionalTestCase,
            optionflags=optionflags),
        ztc.FunctionalDocFileSuite('reference_order.txt',
            package='archetypes.referencebrowserwidget.tests',
            test_class=FunctionalTestCase,
            optionflags=optionflags),
    ])
