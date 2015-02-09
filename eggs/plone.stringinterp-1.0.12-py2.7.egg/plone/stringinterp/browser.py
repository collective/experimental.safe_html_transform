#!/usr/bin/env python
# encoding: utf-8
"""
interfaces.py

Created by Steve McMahon on 2009-09-20.
Copyright (c) 2009 Plone Foundation.
"""

from zope.component import getGlobalSiteManager

from Products.Five import BrowserView

from plone.stringinterp.interfaces import IStringSubstitution
from plone.stringinterp import _


class SubstitutionInfo(BrowserView):
    """
    Browser view support for listing IStringSubstitution
    adapters.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def substitutionList(self):
        """
        returns sequence:
        [ {'category':categoryTitle,
           'items':[{'id':subId, 'description':subDescription}, ...]), ...  ]
        """

        adapters = [a for a in getGlobalSiteManager().registeredAdapters()
                      if len(a.required)==1 and
                         IStringSubstitution.implementedBy(a.factory)]

        # rearrange into categories
        categories = {}
        for a in adapters:
            id = a.name
            cat = getattr(a.factory, 'category', _(u'Miscellaneous'))
            desc = getattr(a.factory, 'description', u'')
            categories.setdefault(cat, []).append(
              {'id': id, 'description': desc})

        # rearrange again into a sorted list
        res = []
        keys = categories.keys()
        # sort, ignoring case
        keys.sort(lambda a, b: cmp(a.lower(), b.lower()))
        for key in keys:
            acat = categories[key]
            # sort by id, ignoring case
            acat.sort(lambda a, b: cmp(a['id'].lower(), b['id'].lower()))
            res.append({'category': key, 'items': acat})

        return res
