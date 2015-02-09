import doctest
import unittest

optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


def test_suite():
    return unittest.TestSuite([
        doctest.DocFileSuite('README.txt',
                             optionflags=optionflags,)
        ])
