#!/usr/bin/env python
# encoding: utf-8
"""
dollarReplace.py

Created by Steve McMahon on 2009-08-13.
Copyright (c) 2009 Plone Foundation.
"""

import string

from zope.interface import implements
from zope.component import adapts, getAdapter, ComponentLookupError

from AccessControl import Unauthorized

from Products.CMFCore.interfaces import IContentish

from plone.stringinterp.interfaces import IStringSubstitution, IStringInterpolator


_marker = u'_bad_'

class LazyDict(object):
    """ cached lookup via adapter """

    def __init__(self, context):
        self.context = context
        self._cache = {}

    def __getitem__(self, key):
        if key and key[0] not in ['_', '.']:
            res = self._cache.get(key)
            if res is None:
                try:
                    res = getAdapter(self.context, IStringSubstitution, key)()
                except ComponentLookupError:
                    res = _marker
                except Unauthorized:
                    res = u'Unauthorized'

                self._cache[key] = res

            if res != _marker:
                return res

        raise KeyError(key)


class Interpolator(object):
    adapts(IContentish)
    implements(IStringInterpolator)

    def __init__(self, context):
        self._ldict = LazyDict(context)

    def __call__(self, s):
        return string.Template(s).safe_substitute(self._ldict)
