##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test for missing values.

>>> from Missing import Value

>>> Value != 12
1
>>> 12 != Value
1
>>> u"abc" != Value
1
>>> Value != u"abc"
1

>>> 1 + Value == Value
1
>>> Value + 1 == Value
1
>>> Value == 1 + Value
1
>>> Value == Value + 1
1
>>> Value.__class__
<type 'Missing.Value'>

>>> type(Value())
<type 'Missing.Value'>

>>> from Missing import MV

>>> MV.__class__
<type 'Missing.Value'>
>>> type(MV())
<type 'Missing.Value'>

>>> from Missing import V

>>> V.__class__
<type 'Missing.Value'>
>>> type(V())
<type 'Missing.Value'>
"""

import unittest
from doctest import DocTestSuite

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        ))
