from Products.PloneTestCase import PloneTestCase as ptc
import unittest
import doctest
from Testing import ZopeTestCase as ztc



ptc.setupPloneSite()

def test_suite():
    optionflags =  (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
    return unittest.TestSuite([
        ztc.ZopeDocFileSuite('widgets/datecomponents.txt',
                             package='plone.app.form',
                             test_class=ptc.FunctionalTestCase,
                             optionflags=optionflags),
        ])
