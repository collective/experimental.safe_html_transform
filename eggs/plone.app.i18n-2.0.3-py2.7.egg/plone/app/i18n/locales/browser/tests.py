# -*- coding: UTF-8 -*-

import unittest

from zope.component.testing import setUp, tearDown
from zope.testing import doctest
from zope.testing.doctestunit import DocTestSuite


def test_suite():
    return unittest.TestSuite((
        DocTestSuite('plone.app.i18n.locales.browser.selector',
                     setUp=setUp(),
                     tearDown=tearDown,
                     optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE),
        ))
