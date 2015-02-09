from unittest import TestSuite
from zope.testing import doctest
from zope.testing.cleanup import cleanUp
from zope.configuration import config
from zope.configuration import xmlconfig
from zope.app.testing import functional
from os.path import join, abspath, dirname


def zcml(source):
    context = config.ConfigurationMachine()
    xmlconfig.registerCommonDirectives(context)
    xmlconfig.string(source, context)

def tearDown(test):
    cleanUp()

testLayer = functional.ZCMLLayer(
    join(abspath(dirname(__file__)), 'ftesting.zcml'),
    __name__, 'TestBrowserLayer', allow_teardown=True)

def test_suite():
    flags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS
    readme = functional.FunctionalDocFileSuite('README.txt',
        package='zope.globalrequest', globs={'zcml': zcml},
        optionflags=flags, tearDown=tearDown)
    readme.layer = testLayer
    return TestSuite((readme,))

