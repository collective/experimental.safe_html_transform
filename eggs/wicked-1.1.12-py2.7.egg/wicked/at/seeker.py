from Products.CMFCore.utils import getToolByName
from wicked.interfaces import IWickedQuery, IAmWicked
from wicked.utils import memoizedproperty, memoize, match, packBrain, cleanUID
from zope.interface import implements
from zope.component import adapts

_marker = object()
class AdvQueryMatchingSeeker(object):
    """
    An advanced query specific
    CMFish catalog query handler
    """
    implements(IWickedQuery)
    adapts(IAmWicked)

    chunk = _marker
    normalled = _marker
    scope = _marker

    def __init__(self, context):
        self.context = context
        self.catalog = getToolByName(context, 'portal_catalog')
        self.path = '/'.join(context.aq_inner.aq_parent.getPhysicalPath())

    def evalQ(self, queries, sort=None):
        resultSet = set([])
        for q in queries:
            resultSet.update(set(self.catalog(q)))
        if sort and resultSet:
            sortableResultSet = [tuple([a[b] for b in sort]+[a]) for a in resultSet]
            sortableResultSet.sort(key=lambda x:x[0:-1])
            return [a[-1] for a in sortableResultSet]
        else:
            return [a for a in resultSet]

    def configure(self, chunk, normalled, scope):
        self.chunk = chunk
        self.normalled = normalled
        self.scope = scope

    def _query(self, query, sort=('created',)):
        if sort:
            return self.evalQ(query, sort)
        else:
            return self.evalQ(query)

    def queryUIDs(self, uids):
        return self._query([{'UID': uids}], sort=None)

    @property
    def scopedQuery(self):
        chunk, title = self.chunk, self.title
        query = [{'getId': chunk}, {'Title': title}]
        if not self.scope is _marker:
            # XXX let's move this out of attr storage
            # on the content to at least an annotation
            try:
                scope = getattr(self.context, self.scope, self.scope)
            except TypeError:
                # scope may not be a string
                scope = self.scope
            if callable(scope):
                scope = scope()
            if scope:
                [a.update(path=scope) for a in query]
        return query

    @property
    def basicQuery(self):
        chunk, normalled = self.chunk, self.normalled
        getId = chunk
        self.title = title = '"%s"' % chunk
        query = [{'path': {'query': self.path, 'depth': -1}, 'getId': chunk},
                 {'path': {'query': self.path, 'depth': -1}, 'Title': title},
                 {'path': {'query': self.path, 'depth': -1}, 'getId': normalled}]
        return query

    @property
    @match
    def scopedSearch(self):
        return self._query(self.scopedQuery)

    @property
    @match
    def search(self):
        return self._query(self.basicQuery)

    def _aggquery(self, name, query):
        curr = getattr(self, name, _marker)
        if curr is _marker:
            curr = query
        else:
            curr.extend(query)
        setattr(self, name, curr)
        return curr

    @property
    def bquery(self):
        return self._aggquery('_bquery', self.basicQuery)

    @property
    def squery(self):
        return self._aggquery('_squery', self.scopedQuery)

    # memo prevents dups
    @memoize
    def aggregate(self, link, normalled, scope):
        """
        builds aggregated queries for scoped and basic
        """
        self.configure(link, normalled, scope)
        self.bquery
        self.squery

    @memoizedproperty
    def agg_brains(self):
        """
        aggregregate search returns
        """
        return list(self._query(self._bquery))

    @memoizedproperty
    def agg_scoped_brains(self):
        """
        aggregregate search returns
        """
        return list(self._query(self._squery))

    __call__ = _query
