# -*- coding: utf-8 -*-
"""Functional Doctests for plone.portlet.collection.

   These test are only triggered when Plone 4 (and plone.testing) is installed.
"""
import doctest

import unittest2 as unittest
import pprint

from plone.testing import layered

from plone.portlet.collection.testing import \
    PLONE_PORTLET_COLLECTION_FUNCTIONAL_TESTING


optionflags = (
    doctest.ELLIPSIS |
    doctest.NORMALIZE_WHITESPACE |
    doctest.REPORT_ONLY_FIRST_FAILURE
)
normal_testfiles = [
    'functional.txt',
]


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        layered(doctest.DocFileSuite(test,
                                     optionflags=optionflags,
                                     globs={'pprint': pprint.pprint,
                                            }
                                     ),
                layer=PLONE_PORTLET_COLLECTION_FUNCTIONAL_TESTING)
        for test in normal_testfiles])
    return suite
