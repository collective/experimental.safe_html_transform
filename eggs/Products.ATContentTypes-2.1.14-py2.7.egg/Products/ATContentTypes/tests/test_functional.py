# -*- coding: UTF-8 -*-

from Products.ATContentTypes.tests.atcttestcase import ATCTFunctionalSiteTestCase

FILES = [
    'topictool.txt', 'portaltype_criterion.txt', 'webdav.txt', 'http_access.txt',
    'reindex_sanity.txt', 'uploading.txt', 'browser_collection_views.txt',
    # traversal.txt registers the browser page "document_view", and this registration
    # stays active in different doctests, so we make sure to include it last.
    'traversal.txt',
]

import doctest
OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE |
               doctest.REPORT_NDIFF)


def test_suite():
    import unittest
    suite = unittest.TestSuite()
    from Testing.ZopeTestCase import FunctionalDocFileSuite as FileSuite
    for testfile in FILES:
        suite.addTest(FileSuite(testfile,
                                optionflags=OPTIONFLAGS,
                                package="Products.ATContentTypes.tests",
                                test_class=ATCTFunctionalSiteTestCase)
                     )
    return suite
