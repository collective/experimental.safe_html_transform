try:
    import unittest2 as unittest
except ImportError: # Python 2.7
    import unittest
import doctest

import zope.component.testing

import os.path

from pkg_resources import get_distribution
from OFS.SimpleItem import SimpleItem
from ZPublisher.Iterators import filestream_iterator

# This is somewhat retarted. We execute README.txt as a doctest, mainly just
# to test that the code samples import cleanly and are valid Python. However,
# in there we also have a code sample of a doctest, which gets executed by the
# doctest runner. Since the method inside the example code block is not yet
# defined when the doctest example is encountered, we get a NameError.
#
# To get around this, we define a fake method and stick it into the globs for
# the doctest.
def _canOutrunKlingons(warpDrive):
    return warpDrive.maxSpeed > 8.0

class DummyUtility(object):
    def __repr__(self):
        return "<Dummy utility>"

class DummyView(object):
    def __init__(self, context, request):
        pass
    def __call__(self):
        return u""

class DummyFile(SimpleItem):
    def __call__(self):
        path = get_distribution('plone.testing').location
        path = os.path.join(path, 'plone', 'testing', 'z2.txt')

        request = self.REQUEST
        response = request.response
        response.setHeader('Content-Type', 'text/plain')
        response.setHeader('Content-Length', os.path.getsize(path))
        return filestream_iterator(path)

def setUp(self):
    zope.component.testing.setUp()

def tearDown(self):
    zope.component.testing.tearDown()

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests([
        doctest.DocFileSuite(
            'layer.txt',
            'zca.txt',
            'security.txt',
            'publisher.txt',
            'zodb.txt',
            'z2.txt',
            setUp=setUp,
            tearDown=tearDown,
            optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE,
        ),
        doctest.DocFileSuite(
            'README.rst',
            globs={'canOutrunKlingons': _canOutrunKlingons,},
            setUp=setUp,
            tearDown=tearDown,
            optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE,
        ),
    ])
    return suite
