import doctest
import unittest

import zope.component.testing


def test_suite():
    return unittest.TestSuite((
        
        doctest.DocFileSuite('alterego.txt',
                     # setUp=setUp,
                     tearDown=zope.component.testing.tearDown),
        
        ))