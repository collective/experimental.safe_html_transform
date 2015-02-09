import unittest
from zope.testing import doctest
import zope.component.testing

def test_suite():

    return unittest.TestSuite((
            doctest.DocFileSuite(
                'message.txt',
                tearDown=zope.component.testing.tearDown(),
                optionflags=doctest.ELLIPSIS
            ),
            doctest.DocFileSuite(
                'fields.txt',
                tearDown=zope.component.testing.tearDown(),
                optionflags=doctest.ELLIPSIS
            ),
            doctest.DocFileSuite(
                'supermodel.txt',
                tearDown=zope.component.testing.tearDown(),
                optionflags=doctest.ELLIPSIS
            ),
        ))
