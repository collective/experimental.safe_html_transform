import logging

from App.special_dtml import DTMLFile
from BTrees.IIBTree import IISet, IITreeSet, intersection, union, multiunion
from BTrees.OOBTree import OOBTree
from BTrees.OIBTree import OIBTree
from zope.interface import implements

from Products.PluginIndexes.common.util import parseIndexRequest
from Products.PluginIndexes.common import safe_callable
from Products.PluginIndexes.interfaces import ILimitedResultIndex
from Products.PluginIndexes.PathIndex.PathIndex import PathIndex

_marker = []
logger = logging.getLogger('ExtendedPathIndex')


class ExtendedPathIndex(PathIndex):
    """A path index stores all path components of the physical path of an
    object.

    Internal datastructure (regular pathindex):

    - a physical path of an object is split into its components

    - every component is kept as a key of a OOBTree in self._indexes

    - the value is a mapping 'level of the path component' to
      'all docids with this path component on this level'

    In addition

    - there is a terminator (None) signifying the last component in the path

    - 2 additional indexes map absolute path to either the doc id or doc ids of
      contained objects. This allows for rapid answering of common queries.
    """

    implements(ILimitedResultIndex)

    meta_type = "ExtendedPathIndex"

    manage_options = (
        {'label': 'Settings', 'action': 'manage_main'},
    )

    indexed_attrs = None
    query_options = ("query", "level", "operator",
                     "depth", "navtree", "navtree_start")

    def __init__(self, id, extra=None, caller=None):
        """ ExtendedPathIndex supports indexed_attrs """
        PathIndex.__init__(self, id, caller)

        if isinstance(extra, dict):
            attrs = extra.get('indexed_attrs', None)
        else:
            attrs = getattr(extra, 'indexed_attrs', None)

        if attrs is None:
            return

        if isinstance(attrs, str):
            attrs = attrs.split(',')
        attrs = filter(None, [a.strip() for a in attrs])

        if attrs:
            # We only index the first attribute so snip off the rest
            self.indexed_attrs = tuple(attrs[:1])

    def clear(self):
        PathIndex.clear(self)
        self._index_parents = OOBTree()
        self._index_items = OIBTree()

    def index_object(self, docid, obj, threshold=100):
        """ hook for (Z)Catalog """

        # PathIndex first checks for an attribute matching its id and
        # falls back to getPhysicalPath only when failing to get one.
        # If self.indexed_attrs is not None, it's value overrides this behavior

        attrs = self.indexed_attrs
        index = attrs is None and self.id or attrs[0]

        path = getattr(obj, index, None)
        if path is not None:
            if safe_callable(path):
                path = path()

            if not isinstance(path, (str, tuple)):
                raise TypeError('path value must be string or tuple '
                                'of strings: (%r, %s)' % (index, repr(path)))
        else:
            try:
                path = obj.getPhysicalPath()
            except AttributeError:
                return 0

        if isinstance(path, (list, tuple)):
            path = '/' + '/'.join(path[1:])
        comps = filter(None, path.split('/'))

        # Make sure we reindex properly when path change
        old_path = self._unindex.get(docid, _marker)
        if old_path is not _marker:
            if old_path != path:
                self.unindex_object(docid, _old=old_path)
                # unindex reduces length, we need to counter that
                self._length.change(1)
        else:
            # We only get a new entry if the value wasn't there before.
            # If it already existed the length is unchanged
            self._length.change(1)

        for i, comp in enumerate(comps):
            self.insertEntry(comp, docid, i)

        # Add terminator
        self.insertEntry(None, docid, len(comps) - 1)

        # Add full-path indexes, to optimize certain edge cases
        parent_path = '/' + '/'.join(comps[:-1])
        parents = self._index_parents.get(parent_path, _marker)
        if parents is _marker:
            self._index_parents[parent_path] = parents = IITreeSet()
        parents.insert(docid)
        self._index_items[path] = docid

        self._unindex[docid] = path
        return 1

    def unindex_object(self, docid, _old=_marker):
        """ hook for (Z)Catalog """

        if _old is not _marker:
            old_value = _old
        else:
            old_value = self._unindex.get(docid, _marker)
            if old_value is _marker:
                logger.log(logging.INFO,
                           'Attempt to unindex nonexistent object with id '
                           '%s' % docid)
                return

        # There is an assumption that paths start with /
        comps = filter(None, old_value.split('/'))

        def unindex(comp, level, docid=docid):
            index_comp = self._index[comp]
            index_comp[level].remove(docid)
            if not index_comp[level]:
                del index_comp[level]
            if not index_comp:
                del self._index[comp]

        try:
            for level, comp in enumerate(comps):
                unindex(comp, level)

            # Remove the terminator
            unindex(None, len(comps) - 1)

            # Remove full-path indexes
            parent_path = '/' + '/'.join(comps[:-1])
            parents = self._index_parents.get(parent_path, _marker)
            if parents is not _marker:
                parents.remove(docid)
                if not parents:
                    del self._index_parents[parent_path]
            del self._index_items['/'.join([parent_path, comps[-1]])]
        except KeyError:
            logger.log(logging.INFO,
                       'Attempt to unindex object with id '
                       '%s failed' % docid)

        self._length.change(-1)
        del self._unindex[docid]

    def search(self, path, default_level=0, depth=-1, navtree=0,
               navtree_start=0, resultset=None):
        """
        path is either a string representing a relative URL or a part of a
        relative URL or a tuple (path, level).

        default_level specifies the level to use when no more specific level
        has been passed in with the path.

        level >= 0  starts searching at the given level
        level <  0  finds matches at *any* level

        depth let's you limit the results to items at most depth levels deeper
        than the matched path. depth == 0 means no subitems are included at
        all, with depth == 1 only direct children are included, etc.
        depth == -1, the default, returns all children at any depth.

        navtree is treated as a boolean; if it evaluates to True, not only the
        query match is returned, but also each container in the path. If depth
        is greater than 0, also all siblings of those containers, as well as
        the siblings of the match are included as well, plus *all* documents at
        the starting level.

        navtree_start limits what containers are included in a navtree search.
        If greater than 0, only containers (and possibly their siblings) at
        that level and up will be included in the resultset.

        """
        if isinstance(path, basestring):
            level = default_level
        else:
            level = int(path[1])
            path = path[0]

        if level < 0:
            # Search at every level, return the union of all results
            return multiunion(
                [self.search(path, level, depth, navtree, navtree_start)
                 for level in xrange(self._depth + 1)])

        comps = filter(None, path.split('/'))

        if navtree and depth == -1:  # Navtrees don't do recursive
            depth = 1

        # Optimizations

        pathlength = level + len(comps) - 1
        if navtree and navtree_start > min(pathlength + depth, self._depth):
            # This navtree_start excludes all items that match the depth
            return IISet()

        if level == 0 and depth in (0, 1):
            # We have easy indexes for absolute paths where
            # we are looking for depth 0 or 1 result sets
            if navtree:
                # Optimized absolute path navtree and breadcrumbs cases
                result = []
                add = lambda x: x is not None and result.append(x)
                if depth == 1:
                    # Navtree case, all sibling elements along the path
                    convert = multiunion
                    index = self._index_parents
                else:
                    # Breadcrumbs case, all direct elements along the path
                    convert = IISet
                    index = self._index_items
                # Collect all results along the path
                for i in range(len(comps), navtree_start - 1, -1):
                    parent_path = '/' + '/'.join(comps[:i])
                    add(index.get(parent_path))
                return convert(result)

            if not path.startswith('/'):
                path = '/' + path
            if depth == 0:
                # Specific object search
                res = self._index_items.get(path)
                return res and IISet([res]) or IISet()
            else:
                # Single depth search
                return self._index_parents.get(path, IISet())

        # Avoid using the root set
        # as it is common for all objects anyway and add overhead
        # There is an assumption about all indexed values having the
        # same common base path
        if level == 0:
            indexpath = list(filter(None, self.getPhysicalPath()))
            minlength = min(len(indexpath), len(comps))
            # Truncate path to first different element
            for i in xrange(minlength):
                if indexpath[i] != comps[i]:
                    break
                level += 1
            comps = comps[level:]

        if not comps and depth == -1:
            # Recursive search for everything
            return IISet(self._unindex)

        # Core application of the indexes
        pathset = None
        depthset = None  # For limiting depth

        if navtree and depth > 0:
            # Include the elements up to the matching path
            depthset = multiunion([
                self._index.get(None, {}).get(i, IISet())
                for i in range(min(navtree_start, level),
                               max(navtree_start, level) + 1)])

        indexedcomps = enumerate(comps)
        if not navtree:
            # Optimize relative-path searches by starting with the
            # presumed smaller sets at the end of the path first
            # We can't do this for the navtree case because it needs
            # the bigger rootset to include siblings along the way.
            indexedcomps = list(indexedcomps)
            indexedcomps.reverse()

        for i, comp in indexedcomps:
            # Find all paths that have comp at the given level
            res = self._index.get(comp, {}).get(i + level)
            if res is None:
                # Non-existing path; navtree is inverse, keep going
                pathset = IISet()
                if not navtree:
                    return pathset
            pathset = intersection(pathset, res)

            if navtree and i + level >= navtree_start:
                depthset = union(depthset, intersection(pathset,
                    self._index.get(None, {}).get(i + level)))

        if depth >= 0:
            # Limit results to those that terminate within depth levels
            start = len(comps) - 1
            if navtree:
                start = max(start, (navtree_start - level))
            depthset = multiunion(filter(None, [depthset] + [
                intersection(pathset, self._index.get(None, {}).get(i + level))
                for i in xrange(start, start + depth + 1)]))

        if navtree or depth >= 0:
            return depthset
        return pathset

    def _apply_index(self, request, resultset=None):
        """ hook for (Z)Catalog
            'request' --  mapping type (usually {"path": "..." }
             additionaly a parameter "path_level" might be passed
             to specify the level (see search())
        """

        record = parseIndexRequest(request, self.id, self.query_options)
        if record.keys == None:
            return None

        level = record.get("level", 0)
        operator = record.get('operator', self.useOperator).lower()
        depth = getattr(record, 'depth', -1)  # use getattr to get 0 value
        navtree = record.get('navtree', 0)
        navtree_start = record.get('navtree_start', 0)

        # depending on the operator we use intersection of union
        if operator == "or":
            set_func = union
        else:
            set_func = intersection

        result = None
        for k in record.keys:
            rows = self.search(k, level, depth, navtree, navtree_start,
                               resultset=resultset)
            result = set_func(result, rows)

        if result:
            return (result, (self.id, ))
        else:
            return (IISet(), (self.id, ))

    def getIndexSourceNames(self):
        """ return names of indexed attributes """
        attrs = self.indexed_attrs or ('getPhysicalPath', )
        return tuple(attrs)

manage_addExtendedPathIndexForm = DTMLFile('dtml/addExtendedPathIndex',
                                           globals())


def manage_addExtendedPathIndex(self, id, extra=None, REQUEST=None,
                                RESPONSE=None, URL3=None):
    """Add an extended path index"""
    return self.manage_addIndex(id, 'ExtendedPathIndex', extra=extra,
                REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)
