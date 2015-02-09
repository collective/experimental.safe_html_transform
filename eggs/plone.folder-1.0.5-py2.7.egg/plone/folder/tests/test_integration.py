from StringIO import StringIO
from Acquisition import Implicit
from transaction import savepoint
from Testing.ZopeTestCase import ZopeTestCase
from zope.interface import implements
from plone.folder.interfaces import IOrderable
from plone.folder.ordered import OrderedBTreeFolderBase
from plone.folder.tests.layer import PloneFolderLayer


class DummyFolder(OrderedBTreeFolderBase, Implicit):
    """ we need to mix in acquisition """
    implements(IOrderable)

    meta_type = 'DummyFolder'


class IntegrationTests(ZopeTestCase):

    layer = PloneFolderLayer

    def testExportDoesntIncludeParent(self):
        self.app._setOb('foo', DummyFolder('foo'))
        foo = self.app.foo
        foo['bar'] = DummyFolder('bar')
        savepoint(optimistic=True)      # savepoint assigns oids
        # now let's export to a buffer and check the objects...
        exp = StringIO()
        self.app._p_jar.exportFile(foo.bar._p_oid, exp)
        self.failUnless('bar' in exp.getvalue())
        self.failIf('foo' in exp.getvalue())


def test_suite():
    from unittest import defaultTestLoader
    return defaultTestLoader.loadTestsFromName(__name__)
