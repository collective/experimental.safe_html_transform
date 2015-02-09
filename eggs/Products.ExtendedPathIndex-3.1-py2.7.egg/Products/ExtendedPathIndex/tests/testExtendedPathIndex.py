import AccessControl  # here to avoid cyclic import
AccessControl  # pyflakes

import unittest

from BTrees.IIBTree import IISet
from BTrees.IIBTree import intersection


class Dummy:

    def __init__(self, path):
        self.path = path

    def getPhysicalPath(self):
        return self.path.split('/')


class TestExtendedPathIndex(unittest.TestCase):
    """ Test ExtendedPathIndex objects """

    def setUp(self):
        self._index = self._makeOne()
        self._values = {
            1: Dummy("/1.html"),
            2: Dummy("/aa/2.html"),
            3: Dummy("/aa/aa/3.html"),
            4: Dummy("/aa/aa/aa/4.html"),
            5: Dummy("/aa/bb/5.html"),
            6: Dummy("/aa/bb/aa/6.html"),
            7: Dummy("/aa/bb/bb/7.html"),
            8: Dummy("/aa"),
            9: Dummy("/aa/bb"),
            10: Dummy("/bb/10.html"),
            11: Dummy("/bb/bb/11.html"),
            12: Dummy("/bb/bb/bb/12.html"),
            13: Dummy("/bb/aa/13.html"),
            14: Dummy("/bb/aa/aa/14.html"),
            15: Dummy("/bb/bb/aa/15.html"),
            16: Dummy("/bb"),
            17: Dummy("/bb/bb"),
            18: Dummy("/bb/aa"),
        }

    def _makeOne(self, id='path'):
        from Products.ExtendedPathIndex import ExtendedPathIndex
        return ExtendedPathIndex.ExtendedPathIndex(id)

    def _populateIndex(self):
        for k, v in self._values.items():
            self._index.index_object(k, v)

    def testIndexIntegrity(self):
        self._populateIndex()
        index = self._index._index
        # Check that terminators have been added for all indexed items
        self.assertEqual(list(index[None][0].keys()), [1, 8, 16])
        self.assertEqual(list(index[None][1].keys()), [2, 9, 10, 17, 18])
        self.assertEqual(list(index[None][2].keys()), [3, 5, 11, 13])
        self.assertEqual(list(index[None][3].keys()), [4, 6, 7, 12, 14, 15])

    def testUnIndexError(self):
        self._populateIndex()
        # this should not raise an error
        self._index.unindex_object(-1)

        # nor should this
        self._index._unindex[1] = "/broken/thing"
        self._index.unindex_object(1)

    def test_depth_limit(self):
        self._populateIndex()
        tests = [
            # depth, expected result
            (1, [1, 8, 16]),
            (2, [1, 2, 8, 9, 10, 16, 17, 18]),
            (3, [1, 2, 3, 5, 8, 9, 10, 11, 13, 16, 17, 18]),
            ]

        for depth, results in tests:
            res = self._index._apply_index(dict(
                path=dict(query='/', depth=depth)))
            lst = list(res[0].keys())
            self.assertEqual(lst, results)

    def test_depth_limit_resultset(self):
        self._populateIndex()
        resultset = IISet([1, 2, 3, 4, 8, 16])
        tests = [
            # depth, expected result
            (1, [1, 8, 16]),
            (2, [1, 2, 8, 16]),
            (3, [1, 2, 3, 8, 16]),
            ]

        for depth, results in tests:
            res = self._index._apply_index(dict(
                path=dict(query='/', depth=depth)), resultset=resultset)
            combined = intersection(res[0], resultset)
            lst = list(combined)
            self.assertEqual(lst, results)

    def testDefaultNavtree(self):
        self._populateIndex()
        tests = [
            # path, level, expected results
            ('/', 0, [1, 8, 16]),
            ('/aa', 0, [1, 2, 8, 9, 16]),
            ('/aa', 1, [1, 2, 3, 8, 9, 10, 13, 16, 17, 18]),
            ('/aa/aa', 0, [1, 2, 3, 8, 9, 16]),
            ('/aa/aa/aa', 0, [1, 2, 3, 4, 8, 9, 16]),
            ('/aa/bb', 0, [1, 2, 5, 8, 9, 16]),
            ('/bb', 0, [1, 8, 10, 16, 17, 18]),
            ('/bb/aa', 0, [1, 8, 10, 13, 16, 17, 18]),
            ('/bb/bb', 0, [1, 8, 10, 11, 16, 17, 18]),
            ]
        for path, level, results in tests:
            res = self._index._apply_index(dict(
                path=dict(query=path, level=level, depth=1, navtree=True)))
            lst = list(res[0].keys())
            self.assertEqual(lst, results)

    def testShallowNavtree(self):
        self._populateIndex()
        # With depth 0 we only get the parents
        tests = [
            # path, level, expected results
            ('/', 0, []),
            ('/aa', 0, [8]),
            ('/aa', 1, [18]),
            ('/aa/aa', 0, [8]),
            ('/aa/aa/aa', 0, [8]),
            ('/aa/bb', 0, [8, 9]),
            ('/bb', 0, [16]),
            ('/bb/aa', 0, [16, 18]),
            ('/bb/bb', 0, [16, 17]),
            ('/bb/bb/aa', 0, [16, 17]),
            ]
        for path, level, results in tests:
            res = self._index._apply_index(dict(
                path=dict(query=path, level=level, depth=0, navtree=True)))
            lst = list(res[0].keys())
            self.assertEqual(lst, results)

    def testNonexistingPaths(self):
        self._populateIndex()
        # With depth 0 we only get the parents
        # When getting non existing paths,
        # we should get as many parents as possible when building navtree
        tests = [
            # path, level, expected results
            ('/', 0, []),
            ('/aa', 0, [8]),  # Exists
            ('/aa/x', 0, [8]),  # Doesn't exist
            ('/aa', 1, [18]),
            ('/aa/x', 1, [18]),
            ('/aa/aa', 0, [8]),
            ('/aa/aa/x', 0, [8]),
            ('/aa/bb', 0, [8, 9]),
            ('/aa/bb/x', 0, [8, 9]),
            ('/aa/bb/x/y/z', 0, [8, 9]),
            ]
        for path, level, results in tests:
            res = self._index._apply_index(dict(
                path=dict(query=path, level=level, depth=0, navtree=True)))
            lst = list(res[0].keys())
            self.assertEqual(lst, results)

    def testEmptyFolderDepthOne(self):
        # Shouldn't return folder when we want children of empty folder
        self._values = {
            1: Dummy("/portal/emptyfolder"),
            2: Dummy("/portal/folder"),
            3: Dummy("/portal/folder/document"),
            4: Dummy("/portal/folder/subfolder"),
            5: Dummy("/portal/folder/subfolder/newsitem"),
        }
        self._populateIndex()
        tests = [
            # path, expected results
            ('/portal/folder', [3, 4]),
            ('/portal/emptyfolder', []),
            ('/portal/folder/document', []),
            ('/portal/folder/subfolder', [5]),
            ('/portal/folder/subfolder/newsitem', []),
            ]
        for path, results in tests:
            res = self._index._apply_index(dict(
                path=dict(query=path, depth=1)))
            lst = list(res[0].keys())
            self.assertEqual(lst, results)

    def testSiteMap(self):
        self._values = {
            1: Dummy("/portal/emptyfolder"),
            2: Dummy("/portal/folder"),
            3: Dummy("/portal/folder/document"),
            4: Dummy("/portal/folder/subfolder"),
            5: Dummy("/portal/folder/subfolder/newsitem"),
        }
        self._populateIndex()
        tests = [
            # Path, depth, expected results
            ('/', 1, []),
            ('/', 2, [1, 2]),
            ('/', 3, [1, 2, 3, 4]),
            ('/', 4, [1, 2, 3, 4, 5]),
            ('/', 5, [1, 2, 3, 4, 5]),
            ('/', 6, [1, 2, 3, 4, 5]),
            ]
        for path, depth, results in tests:
            res = self._index._apply_index(dict(
                path=dict(query=path, depth=depth)))
            lst = list(res[0].keys())
            self.assertEqual(lst, results)

    def testBreadCrumbsWithStart(self):
        self._populateIndex()
        # Adding a navtree_start > 0 to a breadcrumb search should generate
        # breadcrumbs back to that level above the root.
        tests = [
            # path, level, navtree_start, expected results
            ('/', 0, 1, []),
            ('/aa', 0, 1, []),
            ('/aa/aa', 0, 1, [8]),
            ('/aa/aa/aa', 0, 1, [8]),
            ('/aa/bb', 0, 1, [8, 9]),
            ('/bb', 0, 1, []),
            ('/bb/aa', 0, 1, [16, 18]),
            ('/bb/aa', 0, 2, []),
            ('/bb/bb', 0, 1, [16, 17]),
            ('/bb/bb', 0, 2, []),
            ('/bb/bb/bb/12.html', 0, 1, [12, 16, 17]),
            ('/bb/bb/bb/12.html', 0, 2, [12, 17]),
            ('/bb/bb/bb/12.html', 0, 3, [12]),
            ('aa', 1, 1, [18]),
            ('aa', 1, 2, []),
            ]
        for path, level, navtree_start, results in tests:
            res = self._index._apply_index(dict(
                path=dict(query=path, level=level, navtree_start=navtree_start,
                          depth=0, navtree=True)))
            lst = list(res[0].keys())
            self.assertEqual(
                lst, results,
                '%s != %s Failed on %s start %s' % (
                    lst, results, path, navtree_start))

    def testNegativeDepthQuery(self):
        self._populateIndex()
        tests = [
            # path, level, expected results
            ('/', 0, range(1, 19)),
            ('/aa', 0, [2, 3, 4, 5, 6, 7, 8, 9]),
            ('/aa/aa', 0, [3, 4]),
            ('/aa/bb', 0, [5, 6, 7, 9]),
            ('/bb', 0, [10, 11, 12, 13, 14, 15, 16, 17, 18]),
            ('/bb/aa', 0, [13, 14, 18]),
            ('/bb/bb', 0, [11, 12, 15, 17]),
            ('aa', 1, [3, 4, 13, 14, 18]),
        ]

        for path, level, results in tests:
            res = self._index._apply_index(dict(
                path=dict(query=path, level=level)))
            lst = list(res[0].keys())
            self.assertEqual(lst, results,
                '%s != %s Failed on %s level %s' % (
                    lst, results, path, level))

    def testPhysicalPathOptimization(self):
        self._populateIndex()
        # Fake a physical path for the index
        self._index.getPhysicalPath = lambda: ('', 'aa')
        # Test a variety of arguments
        tests = [
            # path, depth, navtree, expected results
            ('/', 1, False, [1, 8, 16]),  # Sitemap
            ('/', 0, True, []),  # Non-Existant
            ('/', 0, True, []),  # Breadcrumb tests
            ('/aa', 0, True, [8]),
            ('/aa/aa', 0, True, [8]),
            ('/', 1, True, [1, 8, 16]),  # Navtree tests
            ('/aa', 1, True, [1, 2, 8, 9, 16]),
            ('/aa/aa', 1, True, [1, 2, 3, 8, 9, 16]),
            ('/', 0, False, []),  # Depth Zero tests
            ('/aa', 0, False, [8]),
            ('/aa/aa', 0, False, []),
            ('/', -1, False, range(1, 19)),  # Depth -1
            ('/aa', -1, False, range(1, 19)),  # Should assume that all
                                               # paths are relevant
            ((('aa/aa', 1), ), -1, False, [4, 14]),  # A (path, level) tuple,
                                                     # relative search
        ]

        for path, depth, navtree, results in tests:
            res = self._index._apply_index(dict(
                path=dict(query=path, depth=depth, navtree=navtree)))
            lst = list(res[0].keys())
            self.assertEqual(
                lst, results,
                '%s != %s Failed on %s depth %s navtree %s' % (
                    lst, results, path, depth, navtree))
