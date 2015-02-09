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
"""interfaces
"""
import zope.interface

class ICircularRelationPath(zope.interface.Interface):
    """A tuple that has a circular relation in the very final element of
    the path."""

    cycled = zope.interface.Attribute(
        """a list of the searches needed to continue the cycle""")

class IQueryFactory(zope.interface.Interface):
    def __call__(query, catalog, cache):
        """if query matches, return `getQueries` callable; else return None.
        
        A getQueries callable receives a relchain.  The last relation token in
        relchain is the most recent, and if you are using search indexes may be
        the only reliable one.  Return an iterable of queries to search
        further from given relchain.
        
        IMPORTANT: the getQueries is first called with an empty tuple.  This
        shou normally yield the original query, but can yield one or more
        arbitrary queries as desired.
        """

class IFilter(zope.interface.Interface):
    def __call__(relchain, query, index, cache):
        """return boolean: whether to accept the given relchain.
        last relation token in relchain is the most recent.
        query is original query that started the search.
        Used for the filter and targetFilter arguments of the IIndex query
        methods.  Cache is a dictionary that will be used throughout a given
        search."""

class IMessageListener(zope.interface.Interface):

    def relationAdded(token, catalog, additions):
        """message: relation token has been added to catalog.
        
        additions is a dictionary of {value name : iterable of added value
        tokens}.
        """

    def relationModified(token, catalog, additions, removals):
        """message: relation token has been updated in catalog.
        
        additions is a dictionary of {value name : iterable of added value
        tokens}.
        removals is a dictionary of {value name : iterable of removed value
        tokens}.
        """

    def relationRemoved(token, catalog, removals):
        """message: relation token has been removed from catalog.
        
        removals is a dictionary of {value name : iterable of removed value
        tokens}.
        """

    def sourceCleared(catalog):
        """message: the catalog has been cleared."""

class IListener(IMessageListener):

    def sourceAdded(catalog):
        """message: you've been added as a listener to the given catalog."""

    def sourceRemoved(catalog):
        """message: you've been removed as a listener from the given catalog.
        """

    def sourceCopied(original, copy):
        """message: the given original is making a copy.
        
        Can install listeners in the copy, if desired.
        """

class ISearchIndex(IMessageListener):

    def copy(catalog):
        """return a copy of this index, bound to provided catalog."""

    def setCatalog(catalog):
        """set the search index to be using the given catalog, return matches.
        
        Should immediately being index up-to-date if catalog has content.
        
        if index already has a catalog, raise an error.
        
        If provided catalog is None, clear catalog and indexes.
        
        Returned matches should be iterable of tuples of (search name or None,
        query names, static values, maxDepth, filter, queryFactory).  Only
        searches matching one of these tuples will be sent to the search
        index.
        """

    def getResults(name, query, maxDepth, filter, queryFactory):
        """return results for search if available, and None if not
        
        Returning a non-None value means that this search index claims the
        search.  No other search indexes will be consulted, and the given
        results are believed to be accurate.
        """

class ICatalog(zope.interface.Interface):

    family = zope.interface.Attribute(
        """BTrees.family32 or BTrees.family64.  Influences defaults.""")

    def index(relation):
        """obtains the token for the relation and indexes"""

    def index_doc(token, relation):
        """indexes relation as given token"""

    def unindex(relation):
        """obtains the token for the relation and unindexes"""

    def unindex_doc(relation):
        """unindexes relation for given token"""

    def __contains__(relation):
        """returns whether the relation is in the index"""

    def __len__():
        """returns number of relations in catalog."""

    def __iter__():
        """return iterator of relations in catalog"""

    def clear():
        """clean catalog to index no relations"""

    def copy(klass=None):
        """return a copy of index, using klass (__new__) if given."""

    def addValueIndex(element, dump=None, load=None, btree=None,
                      multiple=False, name=None):
        """add a value index for given element.
        
        element may be interface element or callable.  Here are the other
        arguments.

        - `dump`, the tokenizer is a callable taking (obj, index, cache)
          and returning a token.  If it is None, that means that the value
          is already a sufficient token.
        
        - `load` is the token resolver, a callable taking (token, index, cache)
          to return the object which the token represents.  If it is None,
          that means that the token is the value.  If you specify None
          for `dump` or `load`, you must also specify None for the other.
        
        - `btree` is the btree module to use to store and process the tokens,
          such as BTrees.OOBTree.  Defaults to catalog.family.IFBTree.

        - `multiple` is a boolean indicating whether the value is a
          collection.

        - `name` is the name of the index in the catalog.  If this is not
          supplied, the element's `__name__` is used.
        """

    def iterValueIndexInfo():
        """return iterable of dicts, each with data for added value indexes.
        
        See arguments to addValueIndex for keys in dicts."""

    def removeValueIndex(name):
        """remove value index of given name"""

    def addListener(listener):
        """add a listener.
        
        Listener is expected to fulfill IListener.
        
        If listener is Persistent, make a weak reference to it."""

    def iterListeners():
        """return iterator of all available listeners"""

    def removeListener(listener):
        """remove listener"""

    def addDefaultQueryFactory(factory):
        """add a default query factory."""

    def iterDefaultQueryFactories():
        """return iterator of all available factories"""

    def removeDefaultQueryFactory(factory):
        """remove factory"""

    def addSearchIndex(ix):
        """add a search index"""

    def iterSearchIndexes():
        """return iterator of all search indexes"""

    def removeSearchIndex(ix):
        """remove search index"""

    def getRelationModuleTools():
        """return dict with useful BTree tools.
        
        keys will include 'BTree', 'Bucket', 'Set', 'TreeSet', 'difference',
        'dump', 'intersection', 'load', and 'union'.  may also include
        'multiunion'.
        """

    def getValueModuleTools(name):
        """return dict with useful BTree tools for named value index.
        
        keys will include 'BTree', 'Bucket', 'Set', 'TreeSet', 'difference',
        'dump', 'intersection', 'load', and 'union'.  may also include
        'multiunion' and other keys for internal use.
        """

    def getRelationTokens(query=None):
        """return tokens for given intransitive query, or all relation tokens.

        Returns a None if no Tokens for query.

        This also happens to be equivalent to `findRelationTokens` with
        a maxDepth of 1, and no other arguments other than the optional
        query, except that if there are no matches, `findRelationTokens`
        returns an empty set (so it *always* returns an iterable). """
    
    def getValueTokens(name, reltoken=None):
        """return value tokens for name, limited to relation token if given.
    
        returns a none if no tokens.
    
        This is identical to `findValueTokens`except that if there are
        no matches, `findValueTokens` returns an empty set (so it
        *always* returns an iterable) """
    
    def yieldRelationTokenChains(query, relData, maxDepth, checkFilter,
                                 checkTargetFilter, getQueries,
                                 findCycles=True):
        """a search workhorse for searches that use a query factory
        
        TODO: explain. :-/"""

    def findValueTokens(
        name, query=None, maxDepth=None, filter=None, targetQuery=None,
        targetFilter=None, queryFactory=None, ignoreSearchIndex=False):
        """find token results for searchTerms.
        - name is the index name wanted for results.
        - if query is None (or evaluates to boolean False), returns the
          underlying btree data structure; which is an iterable result but
          can also be used with BTree operations
        Otherwise, same arguments as findRelationChains.
        """

    def findValues(
        name, query=None, maxDepth=None, filter=None, targetQuery=None,
        targetFilter=None, queryFactory=None, ignoreSearchIndex=False):
        """Like findValueTokens, but resolves value tokens"""

    def findRelations(
        query=(), maxDepth=None, filter=None, targetQuery=None,
        targetFilter=None, queryFactory=None, ignoreSearchIndex=False):
        """Given a single dictionary of {indexName: token}, return an iterable
        of relations that match the query"""

    def findRelationTokens(
        query=(), maxDepth=None, filter=None, targetQuery=None,
        targetFilter=None, queryFactory=None, ignoreSearchIndex=False):
        """Given a single dictionary of {indexName: token}, return an iterable
        of relation tokens that match the query"""

    def findRelationTokenChains(
        query, maxDepth=None, filter=None, targetQuery=None, targetFilter=None,
        queryFactory=None):
        """find tuples of relation tokens for searchTerms.
        - query is a dictionary of {indexName: token}
        - maxDepth is None or a positive integer that specifies maximum depth
          for transitive results.  None means that the transitiveMap will be
          followed until a cycle is detected.  It is a ValueError to provide a
          non-None depth if queryFactory is None and
          index.defaultTransitiveQueriesFactory is None.
        - filter is a an optional callable providing IFilter that determines
          whether relations will be traversed at all.
        - targetQuery is an optional query that specifies that only paths with
          final relations that match the targetQuery should be returned.
          It represents a useful subset of the jobs that can be done with the
          targetFilter.
        - targetFilter is an optional callable providing IFilter that
          determines whether a given path will be included in results (it will
          still be traversed)
        - optional queryFactory takes the place of the index's
          matching registered queryFactory, if any.
        """

    def findRelationChains(
        query, maxDepth=None, filter=None, targetQuery=None, targetFilter=None,
        queryFactory=None):
        "Like findRelationTokenChains, but resolves relation tokens"

    def canFind(query, maxDepth=None, filter=None, targetQuery=None,
                 targetFilter=None, queryFactory=None, ignoreSearchIndex=False):
        """boolean if there is any result for the given search.
        
        Same arguments as findRelationChains.
        
        The general algorithm for using the arguments is this:
        try to yield a single chain from findRelationTokenChains with the
        given arguments.  If one can be found, return True, else False."""

    def tokenizeQuery(query):
        '''Given a dictionary of {indexName: value} returns a dictionary of
        {indexname: token} appropriate for the search methods'''

    def resolveQuery(query):
        '''Given a dictionary of {indexName: token} returns a dictionary of
        {indexname: value}'''

    def tokenizeValues(values, name):
        """Returns an iterable of tokens for the values of the given index
        name"""

    def resolveValueTokens(tokens, name):
        """Returns an iterable of values for the tokens of the given index
        name"""

    def tokenizeRelation(rel):
        """Returns a token for the given relation"""

    def resolveRelationToken(token):
        """Returns a relation for the given token"""

    def tokenizeRelations(rels):
        """Returns an iterable of tokens for the relations given"""

    def resolveRelationTokens(tokens):
        """Returns an iterable of relations for the tokens given"""
