##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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
"""HTTP Publication

$Id: http.py 100362 2009-05-25 16:40:17Z shane $
"""

__docformat__ = 'restructuredtext'

from zope.interface import Attribute
from zope.interface import implements
from zope.publisher.interfaces.http import IHTTPException
from zope.publisher.interfaces.http import MethodNotAllowed
from zope.publisher.publish import mapply
import zope.component

from zope.app.publication.zopepublication import ZopePublication

from zope.publisher.interfaces.http import IMethodNotAllowed #BBB import


class BaseHTTPPublication(ZopePublication):
    """Base for HTTP-based protocol publications"""

    def annotateTransaction(self, txn, request, ob):
        txn = super(BaseHTTPPublication, self).annotateTransaction(
            txn, request, ob)
        request_info = request.method + ' ' + request.getURL()
        txn.setExtendedInfo('request_info', request_info)
        return txn


class HTTPPublication(BaseHTTPPublication):
    """Non-browser HTTP publication"""

    def callObject(self, request, ob):
        # Exception handling, dont try to call request.method
        orig = ob
        if not IHTTPException.providedBy(ob):
            ob = zope.component.queryMultiAdapter((ob, request),
                                                  name=request.method)
            ob = getattr(ob, request.method, None)
            if ob is None:
                raise MethodNotAllowed(orig, request)
        return mapply(ob, request.getPositionalArguments(), request)
