import unittest

from zope.component import provideAdapter
from zope.component import testing

from zope.testing import doctest

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)


def formSetUp(test):
    from zope.formlib.textwidgets import TextWidget
    from zope.formlib.interfaces import IInputWidget
    from zope.publisher.interfaces.browser import IBrowserRequest
    from zope.schema.interfaces import ITextLine
    testing.setUp(test)
    provideAdapter(
        TextWidget, [ITextLine, IBrowserRequest], IInputWidget, )


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            'fieldsets.txt',
            setUp=formSetUp,
            tearDown=testing.tearDown,
            optionflags=OPTIONFLAGS),
        doctest.DocTestSuite(
            'plone.fieldsets.fieldsets'),
        ))
