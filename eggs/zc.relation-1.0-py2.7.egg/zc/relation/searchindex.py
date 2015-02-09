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
import copy
import itertools

import persistent
import BTrees
import zope.interface

import zc.relation.interfaces
import zc.relation.queryfactory
import zc.relation.catalog
import zc.relation.searchindex

##############################################################################
# common case search indexes

_marker = object()

class TransposingTransitiveMembership(persistent.Persistent):
    """for searches using zc.relation.queryfactory.TransposingTransitive.

    Only indexes one direction.  Only indexes with maxDepth=None.
    Does not support filters.

    This search index's algorithm is intended for transposing transitive
    searches that look *downward* in a top-down hierarchy. It could be
    described as indexing transitive membership in a hierarchy--indexing the
    children of a given node.

    This index can significantly speed transitive membership tests,
    demonstrating a factor-of-ten speed increase even in a small example.  See
    timeit/transitive_search_index.py for nitty-gritty details.

    Using it to index the parents in a hierarchy (looking upward) would
    technically work, but it would result in many writes when a top-level node
    changed, and would probably not provide enough read advantage to account
    for the write cost.

    This approach could be used for other query factories that only look
    at the final element in the relchain.  If that were desired, I'd abstract
    some of this code.
    
    while target filters are currently supported, perhaps they shouldn't be:
    the target filter can look at the last element in the relchain, but not
    at the true relchain itself.  That is: the relchain lies, except for the
    last element.
    
    The basic index is for relations.  By providing ``names`` to the
    initialization, the named value indexes will also be included in the
    transitive search index.
    """
    zope.interface.implements(zc.relation.interfaces.ISearchIndex)

    name = index = catalog = None

    def __init__(self, forward, reverse, names=(), static=()):
        # normalize
        self.names = BTrees.family32.OO.Bucket([(nm, None) for nm in names])
        self.forward = forward
        self.reverse = reverse
        self.update = frozenset((forward, reverse))
        self.factory = zc.relation.queryfactory.TransposingTransitive(
            forward, reverse, static)
        for k, v in self.factory.static:
            if isinstance(v, zc.relation.catalog.Any):
                raise NotImplementedError(
                    '``Any`` static values are not supported at this time')

    def copy(self, catalog):
        new = self.__class__.__new__(self.__class__)
        new.names = BTrees.family32.OO.Bucket()
        for nm, val in self.names.items():
            if val is not None:
                new_val = zc.relation.catalog.getMapping(
                    self.catalog.getValueModuleTools(nm))()
                for k, v in val.items():
                    new_val[k] = copy.copy(v)
                val = new_val
            new.names[nm] = val
        new.forward = self.forward
        new.reverse = self.reverse
        new.update = self.update
        new.factory = self.factory
        if self.index is not None:
            new.catalog = catalog
            new.index = zc.relation.catalog.getMapping(
                self.catalog.getRelationModuleTools())()
            for k, v in self.index.items():
                new.index[k] = copy.copy(v)
        new.factory = self.factory
        return new

    def setCatalog(self, catalog):
        if catalog is None:
            self.index = self.catalog = None
            return
        elif self.catalog is not None:
            raise ValueError('catalog already set')
        self.catalog = catalog
        self.index = zc.relation.catalog.getMapping(
            self.catalog.getRelationModuleTools())()
        for nm in self.names.keys():
            self.names[nm] = zc.relation.catalog.getMapping(
                self.catalog.getValueModuleTools(nm))()
        for token in catalog.getRelationTokens():
            if token not in self.index:
                self._index(token)
        # name, query_names, static_values, maxDepth, filter, queryFactory
        res = [(None, (self.forward,), self.factory.static, None, None,
                self.factory)]
        for nm in self.names:
            res.append(
                (nm, (self.forward,), self.factory.static, None, None,
                 self.factory))
        return res

    def _index(self, token, removals=None, remove=False):
        starts = set((token,))
        if removals and self.forward in removals:
            starts.update(t for t in removals[self.forward] if t is not None)
        tokens = set()
        reverseQuery = BTrees.family32.OO.Bucket(
            ((self.reverse, None),) + self.factory.static)
        for token in starts:
            getQueries = self.factory(dict(reverseQuery), self.catalog)
            tokens.update(chain[-1] for chain in
                          self.catalog.yieldRelationTokenChains(
                            reverseQuery, ((token,),), None, None, None,
                            getQueries))
        if remove:
            tokens.remove(token)
            self.index.pop(token, None)
            for ix in self.names.values():
                ix.pop(token, None)
        # because of the possibilty of cycles involving this token in the
        # previous state, we first clean out all of the items "above"
        for token in tokens:
            self.index.pop(token, None)
        # now we go back and try to fill them back in again.  If there had
        # been a cycle, we can see now that we have to work down.
        relTools = self.catalog.getRelationModuleTools()
        query = BTrees.family32.OO.Bucket(
            ((self.forward, None),) + self.factory.static)
        getQueries = self.factory(query, self.catalog)
        for token in tokens:
            if token in self.index: # must have filled it in during a cycle
                continue
            stack = [[token, None, set(), [], set((token,)), False]]
            while stack:
                token, child, sets, empty, traversed_tokens, cycled = stack[-1]
                if not sets:
                    rels = zc.relation.catalog.multiunion(
                        (self.catalog.getRelationTokens(q) for q in
                         getQueries([token])), relTools)
                    for rel in rels:
                        if rel == token:
                            # cycles on itself.
                            sets.add(relTools['Set']((token,)))
                            continue
                        indexed = self.index.get(rel)
                        if indexed is None:
                            iterator = reversed(stack)
                            traversed = [iterator.next()]
                            for info in iterator:
                                if rel == info[0]:
                                    sets = info[2]
                                    traversed_tokens = info[4]
                                    cycled = True
                                    for trav in traversed:
                                        sets.update(trav[2])
                                        trav[2] = sets
                                        traversed_tokens.update(trav[4])
                                        trav[4] = traversed_tokens
                                        trav[5] = True
                                    break
                                traversed.append(info)
                            else:
                                empty.append(rel)
                        else:
                            sets.add(indexed)
                    sets.add(rels)
                if child is not None:
                    sets.add(child)
                    # clear it out
                    child = stack[-1][1] = None
                if empty:
                    # We have one of two classes of situations.  Either this
                    # *is* currently a cycle, and the result for this and all
                    # children will be the same set; or this *may* be
                    # a cycle, because this is an initial indexing.
                    # Walk down, passing token.
                    next = empty.pop()
                    stack.append(
                        [next, None, set(), [], set((next,)), False])
                else:
                    stack.pop()
                    assert stack or not cycled, (
                        'top level should never consider itself cycled')
                    if not cycled:
                        rels = zc.relation.catalog.multiunion(
                            sets, relTools)
                        rels.insert(token)
                        names = {}
                        for nm in self.names.keys():
                            names[nm] = zc.relation.catalog.multiunion(
                                (self.catalog.getValueTokens(nm, rel)
                                 for rel in rels),
                                self.catalog.getValueModuleTools(nm))
                        for token in traversed_tokens:
                            self.index[token] = rels
                            for nm, ix in self.names.items():
                                ix[token] = names[nm]
                        if stack:
                            stack[-1][1] = rels

    # listener interface

    def relationAdded(self, token, catalog, additions):
        if token in self.index and not self.update.intersection(additions):
            return # no changes; don't do work
        self._index(token)

    def relationModified(self, token, catalog, additions, removals):
        if (token in self.index and not self.update.intersection(additions) and
            not self.update.intersection(removals)):
            return # no changes; don't do work
        self._index(token, removals)

    def relationRemoved(self, token, catalog, removals):
        self._index(token, removals, remove=True)

    def sourceCleared(self, catalog):
        if self.catalog is catalog:
            self.setCatalog(None)
            self.setCatalog(catalog)

    # end listener interface

    def getResults(self, name, query, maxDepth, filter, queryFactory):
        rels = self.catalog.getRelationTokens(query)
        if name is None:
            tools = self.catalog.getRelationModuleTools()
            ix = self.index
        else:
            tools = self.catalog.getValueModuleTools(name)
            ix = self.names[name]
        if rels is None:
            return tools['Set']()
        elif not rels:
            return rels
        return zc.relation.catalog.multiunion(
            (ix.get(rel) for rel in rels), tools)


class Intransitive(persistent.Persistent):
    """saves results for precise search.
    
    Could be used for transitive searches, but writes would be much more
    expensive than the TransposingTransitive approach.
    
    see tokens.txt for an example.
    """
    # XXX Rename to Direct?
    zope.interface.implements(
        zc.relation.interfaces.ISearchIndex,
        zc.relation.interfaces.IListener)

    index = catalog = name = queryFactory = None
    update = frozenset()

    def __init__(self, names, name=None,
                 queryFactory=None, getValueTokens=None, update=None,
                 unlimitedDepth=False):
        self.names = tuple(sorted(names))
        self.name = name
        self.queryFactory = queryFactory
        if update is None:
            update = names
            if name is not None:
                update += (name,)
        self.update = frozenset(update)
        self.getValueTokens = getValueTokens
        if unlimitedDepth:
            depths = (1, None)
        else:
            depths = (1,)
        self.depths = tuple(depths)

    def copy(self, catalog):
        res = self.__class__.__new__(self.__class__)
        if self.index is not None:
            res.catalog = catalog
            res.index = BTrees.family32.OO.BTree()
            for k, v in self.index.items():
                res.index[k] = copy.copy(v)
        res.names = self.names
        res.name = self.name
        res.queryFactory = self.queryFactory
        res.update = self.update
        res.getValueTokens = self.getValueTokens
        res.depths = self.depths
        return res

    def setCatalog(self, catalog):
        if catalog is None:
            self.index = self.catalog = None
            return
        elif self.catalog is not None:
            raise ValueError('catalog already set')
        self.catalog = catalog
        self.index = BTrees.family32.OO.BTree()
        self.sourceAdded(catalog)
        # name, query_names, static_values, maxDepth, filter, queryFactory
        return [(self.name, self.names, (), depth, None, self.queryFactory)
                for depth in self.depths]

    def relationAdded(self, token, catalog, additions):
        self._index(token, catalog, additions)

    def relationModified(self, token, catalog, additions, removals):
        self._index(token, catalog, additions, removals)

    def relationRemoved(self, token, catalog, removals):
        self._index(token, catalog, removals=removals, removed=True)

    def _index(self, token, catalog, additions=None, removals=None,
               removed=False):
        if ((not additions or not self.update.intersection(additions)) and
            (not removals or not self.update.intersection(removals))):
            return
        if additions is None:
            additions = {}
        if removals is None:
            removals = {}
        for query in self.getQueries(token, catalog, additions, removals,
                                     removed):
            self._indexQuery(tuple(query.items()))

    def _indexQuery(self, query):
            dquery = dict(query)
            if self.queryFactory is not None:
                getQueries = self.queryFactory(dquery, self.catalog)
            else:
                getQueries = lambda empty: (query,)
            res = zc.relation.catalog.multiunion(
                (self.catalog.getRelationTokens(q) for q in getQueries(())),
                self.catalog.getRelationModuleTools())
            if not res:
                self.index.pop(query, None)
            else:
                if self.name is not None:
                    res = zc.relation.catalog.multiunion(
                        (self.catalog.getValueTokens(self.name, r)
                         for r in res),
                        self.catalog.getValueModuleTools(self.name))
                self.index[query] = res

    def sourceAdded(self, catalog):
        queries = set()
        for token in catalog.getRelationTokens():
            additions = dict(
                (info['name'], catalog.getValueTokens(info['name'], token))
                for info in catalog.iterValueIndexInfo())
            queries.update(
                tuple(q.items()) for q in
                self.getQueries(token, catalog, additions, {}, False))
        for q in queries:
            self._indexQuery(q)

    def sourceRemoved(self, catalog):
        # this only really makes sense if the getQueries/getValueTokens was
        # changed
        queries = set()
        for token in catalog.getRelationTokens():
            removals = dict(
                (info['name'], catalog.getValueTokens(info['name'], token))
                for info in catalog.iterValueIndexInfo())
            queries.update(
                tuple(q.items()) for q in
                self.getQueries(token, catalog, {}, removals, True))
        for q in queries:
            self._indexQuery(q)

    def sourceCleared(self, catalog):
        if self.catalog is catalog:
            self.setCatalog(None)
            self.setCatalog(catalog)

    def sourceCopied(self, original, copy):
        pass

    def getQueries(self, token, catalog, additions, removals, removed):
        source = {}
        for name in self.names:
            values = set()
            for changes in (additions, removals):
                value = changes.get(name, _marker)
                if value is None:
                    values.add(value)
                elif value is not _marker:
                    values.update(value)
            if values:
                if not removed and source:
                    source.clear()
                    break
                source[name] = values
        if removed and not source:
            return
        for name in self.names:
            res = None
            if self.getValueTokens is not None:
                res = self.getValueTokens(self, name, token, catalog, source,
                                          additions, removals, removed)
            if res is None:
                if name in source:
                    continue
                res = set((None,))
                current = self.catalog.getValueTokens(name, token)
                if current:
                    res.update(current)
            source[name] = res
        vals = []
        for name in self.names:
            src = source[name]
            iterator = iter(src)
            value = iterator.next() # should always have at least one
            vals.append([name, value, iterator, src])
        while 1:
            yield BTrees.family32.OO.Bucket(
                [(name, value) for name, value, iterator, src in vals])
            for s in vals:
                name, value, iterator, src = s
                try:
                    s[1] = iterator.next()
                except StopIteration:
                    iterator = s[2] = iter(src)
                    s[1] = iterator.next()
                else:
                    break
            else:
                break

    def getResults(self, name, query, maxDepth, filter, queryFactory):
        query = tuple(query.items())
        for nm, v in query:
            if isinstance(v, zc.relation.catalog.Any):
                return None # TODO open up
        res = self.index.get(query)
        if res is None:
            if self.name is None:
                res = self.catalog.getRelationModuleTools()['Set']()
            else:
                res = self.catalog.getValueModuleTools(self.name)['Set']()
        return res
