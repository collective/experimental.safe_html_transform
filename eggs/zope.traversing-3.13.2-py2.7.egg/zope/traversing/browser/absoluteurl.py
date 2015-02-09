##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Absolute URL View components
"""
import urllib
import zope.component
from zope.interface import implements
from zope.location.interfaces import ILocation
from zope.proxy import sameProxiedObjects
from zope.publisher.browser import BrowserView
from zope.traversing.browser.interfaces import IAbsoluteURL
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('zope')

_insufficientContext = _("There isn't enough context to get URL information. "
                       "This is probably due to a bug in setting up location "
                       "information.")

_safe = '@+' # Characters that we don't want to have quoted

def absoluteURL(ob, request):
    return zope.component.getMultiAdapter((ob, request), IAbsoluteURL)()

class AbsoluteURL(BrowserView):
    implements(IAbsoluteURL)

    def __unicode__(self):
        return urllib.unquote(self.__str__()).decode('utf-8')

    def __str__(self):
        context = self.context
        request = self.request

        # The application URL contains all the namespaces that are at the
        # beginning of the URL, such as skins, virtual host specifications and
        # so on.
        if (context is None
            or sameProxiedObjects(context, request.getVirtualHostRoot())):
            return request.getApplicationURL()

        # first try to get the __parent__ of the object, no matter whether
        # it provides ILocation or not. If this fails, look up an ILocation
        # adapter. This will always work, as a general ILocation adapter
        # is registered for interface in zope.location (a LocationProxy)
        # This proxy will return a parent of None, causing this to fail
        # More specific ILocation adapters can be provided however.
        try:
            container = context.__parent__
        except AttributeError:
            # we need to assign to context here so we can get
            # __name__ from it below
            context = ILocation(context)
            container = context.__parent__

        if container is None:
            raise TypeError(_insufficientContext)

        url = str(zope.component.getMultiAdapter((container, request),
                                                 IAbsoluteURL))
        name = getattr(context, '__name__', None)
        if name is None:
            raise TypeError(_insufficientContext)

        if name:
            url += '/' + urllib.quote(name.encode('utf-8'), _safe)

        return url

    def __call__(self):
        return self.__str__()

    def breadcrumbs(self):
        context = self.context
        request = self.request

        # We do this here do maintain the rule that we must be wrapped
        context = ILocation(context, context)
        container = getattr(context, '__parent__', None)
        if container is None:
            raise TypeError(_insufficientContext)

        if sameProxiedObjects(context, request.getVirtualHostRoot()) or \
               isinstance(context, Exception):
            return ({'name':'', 'url': self.request.getApplicationURL()}, )

        base = tuple(zope.component.getMultiAdapter(
                (container, request), IAbsoluteURL).breadcrumbs())

        name = getattr(context, '__name__', None)
        if name is None:
            raise TypeError(_insufficientContext)

        if name:
            base += ({'name': name,
                      'url': ("%s/%s" % (base[-1]['url'],
                                         urllib.quote(name.encode('utf-8'),
                                                      _safe)))
                      }, )

        return base

class SiteAbsoluteURL(BrowserView):
    implements(IAbsoluteURL)

    def __unicode__(self):
        return urllib.unquote(self.__str__()).decode('utf-8')

    def __str__(self):
        context = self.context
        request = self.request

        if sameProxiedObjects(context, request.getVirtualHostRoot()):
            return request.getApplicationURL()

        url = request.getApplicationURL()
        name = getattr(context, '__name__', None)
        if name:
            url += '/' + urllib.quote(name.encode('utf-8'), _safe)

        return url

    def __call__(self):
        return self.__str__()

    def breadcrumbs(self):
        context = self.context
        request = self.request

        if sameProxiedObjects(context, request.getVirtualHostRoot()):
            return ({'name':'', 'url': self.request.getApplicationURL()}, )

        base = ({'name':'', 'url': self.request.getApplicationURL()}, )

        name = getattr(context, '__name__', None)
        if name:
            base += ({'name': name,
                      'url': ("%s/%s" % (base[-1]['url'],
                                         urllib.quote(name.encode('utf-8'),
                                                      _safe)))
                      }, )

        return base
