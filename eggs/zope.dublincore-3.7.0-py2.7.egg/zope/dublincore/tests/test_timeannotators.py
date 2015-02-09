##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
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
"""Test time annotator.

"""

import doctest
import zope.testing.renormalizing
import re

datetime_re = (
    '[0-9]{4}, [0-9]{1,2}, [0-9]{1,2}, [0-9]{1,2}, [0-9]{1,2}, [0-9]{1,2}, '
    '[0-9]{1,6}')

def test_suite():
    return doctest.DocFileSuite(
        'timeannotators.txt',
        checker=zope.testing.renormalizing.RENormalizing(
            [(re.compile(datetime_re), '<DATETIME>')])
        )