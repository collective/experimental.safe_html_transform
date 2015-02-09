##############################################################################
#
# Copyright (c) 2006-2008 Zope Corporation and Contributors.
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
import persistent
import BTrees
import zope.interface

import zc.relation.interfaces
import zc.relation.catalog

##############################################################################
# a common case transitive queries factory

_marker = object()

class TransposingTransitive(persistent.Persistent):
    zope.interface.implements(zc.relation.interfaces.IQueryFactory)

    def __init__(self, name1, name2, static=()):
        self.names = [name1, name2] # a list so we can use index
        if getattr(static, 'items', None) is not None:
            static = static.items()
        self.static = tuple(sorted(static))

    def __call__(self, query, catalog):
        # check static values, if any.  we want to be permissive here. (as
        # opposed to finding searchindexes in the catalog's
        # _getSearchIndexResults method)
        for k, v in self.static:
            if k in query:
                if isinstance(v, zc.relation.catalog.Any):
                    if isinstance(query[k], zc.relation.catalog.Any):
                        if query[k].source.issubset(v.source):
                            continue
                    elif query[k] in v:
                        continue
                elif v == query[k]:
                    continue
            return None
        static = []
        name = other = _marker
        for nm, val in query.items():
            try:
                ix = self.names.index(nm)
            except ValueError:
                static.append((nm, val))
            else:
                if name is not _marker:
                    # both were specified: no transitive search known.
                    return None
                else:
                    name = nm
                    other = self.names[not ix]
        if name is not _marker:
            def getQueries(relchain):
                if not relchain:
                    yield query
                    return
                if other is None:
                    rels = relchain[-1]
                else:
                    tokens = catalog.getValueTokens(other, relchain[-1])
                    if not tokens:
                        return
                    rels = zc.relation.catalog.Any(tokens)
                res = BTrees.family32.OO.Bucket(static)
                res[name] = rels
                yield res
            return getQueries

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                set(self.names) == set(other.names)
                and self.static == other.static)

    def __ne__(self, other):
        return not self.__eq__(other)
