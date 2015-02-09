import unittest
import doctest

from Testing import ZopeTestCase as ztc
import plone.stringinterp.tests.stringinterpTestCase as tc

testfiles = (
    'substitutionTests.txt',
    'interpolationTests.txt',
)

def test_suite():
    return unittest.TestSuite([

        ztc.FunctionalDocFileSuite(
            f, package='plone.stringinterp.tests',
            test_class=tc.FunctionalTestCase,
            optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)

            for f in testfiles
        ]
    )

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
