"""ZODB-specific helpers and layers
"""

from plone.testing import Layer

def stackDemoStorage(db=None, name=None):
    """Create a new DemoStorage that has the given database as a base.
    ``db`` may be none, in which case a base demo storage will be created.
    ``name`` is optional, but can be used to name the storage.

    The usual pattern in a layer is::

        def setUp(self):
            self['zodbDB'] = stackDemoStorage(self.get('zodbDB'), name='mylayer')

        def tearDown(self):
            self['zodbDB'].close()
            del self['zodbDB']
    """

    from ZODB.DemoStorage import DemoStorage
    from ZODB.DB import DB

    if db is not None:
        storage = DemoStorage(name=name, base=db.storage)
    else:
        storage = DemoStorage(name=name)

    return DB(storage)

class EmptyZODB(Layer):
    """Set up a new ZODB database using ``DemoStorage``. The database object
    is available as the resource ``zodbDB``.

    For each test, a new connection is created, and made available as the
    resource ``zodbConnection``. The ZODB root is available as ``zodbRoot``.
    A new transaction is then begun.

    On test tear-down, the transaction is aborted, the connection closed,
    and the two resources deleted.

    If you want to build your own layer with ZODB functionality, you may
    want to subclass this class and override one or both of
    ``createStorage()`` and ``createDatabase()``.
    """

    defaultBases = ()

    def setUp(self):
        self['zodbDB'] = self.createDatabase(self.createStorage())

    def tearDown(self):
        self['zodbDB'].close()
        del self['zodbDB']

    def testSetUp(self):
        self['zodbConnection'] = connection = self['zodbDB'].open()
        self['zodbRoot']       = connection.root()

        import transaction
        transaction.begin()

    def testTearDown(self):
        import transaction
        transaction.abort()

        self['zodbConnection'].close()

        del self['zodbConnection']
        del self['zodbRoot']

    # Template methods for use in subclasses, if required

    def createStorage(self):
        """Create a new storage.

        You may want to subclass this class when creating a custom layer. You
        can then override this method to create a different storage. The
        default is an empty DemoStorage.
        """

        from ZODB.DemoStorage import DemoStorage
        return DemoStorage(name='EmptyZODB')

    def createDatabase(self, storage):
        """Create a new database from the given storage.

        Like ``createStorage()``, this hook exists for subclasses to override
        as necessary.
        """

        from ZODB.DB import DB
        return DB(storage)

EMPTY_ZODB = EmptyZODB()
