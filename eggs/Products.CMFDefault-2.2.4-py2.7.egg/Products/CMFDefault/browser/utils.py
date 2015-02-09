##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Browser view utilities. """

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.Five import BrowserView
from zope.component import getUtility

from Products.CMFCore.interfaces import IPropertiesTool
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.permissions import View
from Products.CMFDefault.utils import getBrowserCharset
from Products.CMFDefault.utils import toUnicode


def decode(meth):
    def decoded_meth(self, *args, **kw):
        return toUnicode(meth(self, *args, **kw), self._getDefaultCharset())
    return decoded_meth

def memoize(meth):
    def memoized_meth(self, *args):
        if not hasattr(self, '__memo__'):
            self.__memo__ = {}
        sig = (meth, args)
        if sig not in self.__memo__:
            self.__memo__[sig] = meth(self, *args)
        return self.__memo__[sig]
    return memoized_meth


class MacroView(BrowserView):

    """Allows to use macros from non-view templates.
    """
    
    # The following allows to traverse the view/class and reach
    # macros defined in page templates, e.g. in a use-macro.
    security = ClassSecurityInfo()

    def _macros(self):
        return self.index.macros

    security.declareProtected(View, 'macros')
    macros = property(_macros, None, None)

InitializeClass(MacroView)


class ViewBase(BrowserView):

    # helpers

    @memoize
    def _getTool(self, name):
        return getToolByName(self.context, name)

    @memoize
    def _checkPermission(self, permission):
        mtool = self._getTool('portal_membership')
        return mtool.checkPermission(permission, self.context)

    @memoize
    def _getPortalURL(self):
        utool = self._getTool('portal_url')
        return utool()

    @memoize
    def _getViewURL(self):
        return self.request['ACTUAL_URL']

    @memoize
    def _getDefaultCharset(self):
        ptool = getUtility(IPropertiesTool)
        return ptool.getProperty('default_charset', None)

    @memoize
    def _getBrowserCharset(self):
        return getBrowserCharset(self.request)

    # interface

    @memoize
    @decode
    def title(self):
        return self.context.Title()

    @memoize
    @decode
    def description(self):
        return self.context.Description()
