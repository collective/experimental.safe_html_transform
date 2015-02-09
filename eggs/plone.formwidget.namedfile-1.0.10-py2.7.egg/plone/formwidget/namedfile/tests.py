###############################################################################
#
# Copyright 2006 by refline (Schweiz) AG, CH-5630 Muri
#
###############################################################################

"""
$Id: tests.py 86815 2008-05-17 00:53:17Z pcardune $
"""
__docformat__ = "reStructuredText"

import doctest
import unittest
from zope.testing.doctestunit import DocFileSuite

from z3c.form import testing

def test_suite():
    return unittest.TestSuite((
        DocFileSuite('widget.txt',
                     setUp=testing.setUp, tearDown=testing.tearDown,
                     optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS,
                     ),
        ))
