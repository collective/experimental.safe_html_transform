import unittest


class MockItem(object):

    def getId(self):
        return 'mock'

    def getPhysicalPath(self):
        return ('', 'foo', 'bar', 'baz')

    def getCustomPath(self):
        return ('', 'custom', 'path')

    def getStringPath(self):
        return '/string/path'


class IndexedAttrsTests(unittest.TestCase):

    def _makeOne(self, attr='path', *args, **kw):
        from Products.ExtendedPathIndex import ExtendedPathIndex
        return ExtendedPathIndex.ExtendedPathIndex(attr, *args, **kw)

    def testDefaultIndexedAttrs(self):
        # By default we don't have indexed_attrs at all
        index = self._makeOne()
        self.assertTrue(index.indexed_attrs is None)

    def testDefaultIndexSourceNames(self):
        # However, getIndexSourceName returns 'getPhysicalPath'
        index = self._makeOne()
        self.assertEqual(index.getIndexSourceNames(), ('getPhysicalPath', ))

    def testDefaultIndexObject(self):
        # By default PathIndex indexes getPhysicalPath
        index = self._makeOne()
        index.index_object(123, MockItem())
        self.assertEqual(index.getEntryForObject(123), '/foo/bar/baz')

    def testExtraAsRecord(self):
        # 'extra' can either be an instance
        class Record(object):
            def __init__(self, **kw):
                self.__dict__.update(kw)

        index = self._makeOne(extra=Record(indexed_attrs='getCustomPath'))
        self.assertEqual(index.indexed_attrs, ('getCustomPath', ))

    def testExtraAsMapping(self):
        # or a dictionary
        index = self._makeOne(extra=dict(indexed_attrs='getCustomPath'))
        self.assertEqual(index.indexed_attrs, ('getCustomPath', ))

    def testCustomIndexSourceNames(self):
        # getIndexSourceName returns the indexed_attrs
        index = self._makeOne(extra=dict(indexed_attrs='getCustomPath'))
        self.assertEqual(index.getIndexSourceNames(), ('getCustomPath', ))

    def testCustomIndexObject(self):
        # PathIndex indexes getCustomPath
        index = self._makeOne(extra=dict(indexed_attrs='getCustomPath'))
        index.index_object(123, MockItem())
        self.assertEqual(index.getEntryForObject(123), '/custom/path')

    def testStringIndexObject(self):
        # PathIndex accepts a path as tuple or string
        index = self._makeOne(extra=dict(indexed_attrs='getStringPath'))
        index.index_object(123, MockItem())
        self.assertEqual(index.getEntryForObject(123), '/string/path')

    def testIdIndexObject(self):
        # PathIndex prefers an attribute matching its id over getPhysicalPath
        index = self._makeOne('getId')
        index.index_object(123, MockItem())
        self.assertEqual(index.getEntryForObject(123), 'mock')

    def testIdAndIndexedAttrsObject(self):
        # Using indexed_attr overrides this behavior
        index = self._makeOne('getId',
                              extra=dict(indexed_attrs='getCustomPath'))
        index.index_object(123, MockItem())
        self.assertEqual(index.getEntryForObject(123), '/custom/path')

    def testListIndexedAttr(self):
        # indexed_attrs can be a list
        index = self._makeOne(
            'getId', extra=dict(indexed_attrs=['getCustomPath', 'foo']))
        # only the first attribute is used
        self.assertEqual(index.getIndexSourceNames(), ('getCustomPath', ))

    def testStringIndexedAttr(self):
        # indexed_attrs can also be a comma separated string
        index = self._makeOne(
            'getId', extra=dict(indexed_attrs='getCustomPath, foo'))
        # only the first attribute is used
        self.assertEqual(index.getIndexSourceNames(), ('getCustomPath', ))

    def testEmtpyListAttr(self):
        # Empty indexed_attrs falls back to defaults
        index = self._makeOne('getId', extra=dict(indexed_attrs=[]))
        self.assertEqual(index.getIndexSourceNames(), ('getPhysicalPath', ))

    def testEmtpyStringAttr(self):
        # Empty indexed_attrs falls back to defaults
        index = self._makeOne('getId', extra=dict(indexed_attrs=''))
        self.assertEqual(index.getIndexSourceNames(), ('getPhysicalPath', ))
