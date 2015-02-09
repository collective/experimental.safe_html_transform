import zope.interface
import zope.component
import zope.testing.doctest
import unittest

OPTIONFLAGS = (zope.testing.doctest.ELLIPSIS |
               zope.testing.doctest.NORMALIZE_WHITESPACE)

from common import setUp
from common import tearDown


def test_suite():
    globs = dict(
        interface=zope.interface,
        component=zope.component)

    return unittest.TestSuite((
        zope.testing.doctest.DocFileSuite(
            'README.txt',
            optionflags=OPTIONFLAGS,
            setUp=setUp,
            tearDown=tearDown,
            globs=globs,
            package="z3c.jbot"),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
