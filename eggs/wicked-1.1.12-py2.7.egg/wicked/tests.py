def test_suite():
    import unittest, doctest
    from Testing.ZopeTestCase import ZopeDocFileSuite
    try:
        from Products.PloneTestCase.layer import ZCMLLayer
    except ImportError:
        from collective.testing.layer import ZCMLLayer
    from wicked.utils import test_suite as utilsuite
    from wicked.link import test_suite as linksuite

    cachemanager = ZopeDocFileSuite('cache.txt',
                                    package='wicked',
                                    optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
                                    )
    cachemanager.layer = ZCMLLayer
    return unittest.TestSuite((utilsuite(), linksuite(), cachemanager))
