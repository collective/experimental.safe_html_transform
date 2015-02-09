##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
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

import unittest

from ZODB.tests import StorageTestBase
from ZODB.tests import BasicStorage
from ZODB.tests import Synchronization
from ZODB.tests import ConflictResolution
from ZODB.tests import MTStorage


class ZODBProtocolTests(StorageTestBase.StorageTestBase,
                        BasicStorage.BasicStorage,
                        Synchronization.SynchronizedStorage,
                        ConflictResolution.ConflictResolvingStorage,
                        MTStorage.MTStorage,
                       ):

    def setUp(self):
        StorageTestBase.StorageTestBase.setUp(self)
        self.open()

    def open(self, **kwargs):
        from tempstorage.TemporaryStorage import TemporaryStorage
        self._storage = TemporaryStorage('foo')

    def check_tid_ordering_w_commit(self):
        # The test uses invalid test data of 'x'. The normal storages
        # don't load the actual data and thus pass, but the tempstorage
        # will always try to load the data and fail
        pass


class TemporaryStorageTests(unittest.TestCase):

    def _getTargetClass(self):
        from tempstorage.TemporaryStorage import TemporaryStorage
        return TemporaryStorage

    def _makeOne(self, name='foo'):
        return self._getTargetClass()(name)

    def _dostore(self, storage, oid=None, revid=None, data=None,
                 already_pickled=0, user=None, description=None):
        # Borrowed from StorageTestBase, to allow passing storage.
        """Do a complete storage transaction.  The defaults are:

         - oid=None, ask the storage for a new oid
         - revid=None, use a revid of ZERO
         - data=None, pickle up some arbitrary data (the integer 7)

        Returns the object's new revision id.
        """
        import transaction
        from ZODB.tests.MinPO import MinPO

        if oid is None:
            oid = storage.new_oid()
        if revid is None:
            revid = StorageTestBase.ZERO
        if data is None:
            data = MinPO(7)
        if type(data) == int:
            data = MinPO(data)
        if not already_pickled:
            data = StorageTestBase.zodb_pickle(data)
        # Begin the transaction
        t = transaction.Transaction()
        if user is not None:
            t.user = user
        if description is not None:
            t.description = description
        try:
            storage.tpc_begin(t)
            # Store an object
            r1 = storage.store(oid, revid, data, '', t)
            # Finish the transaction
            r2 = storage.tpc_vote(t)
            revid = StorageTestBase.handle_serials(oid, r1, r2)
            storage.tpc_finish(t)
        except:
            storage.tpc_abort(t)
            raise
        return revid

    def _do_read_conflict(self, db, mvcc):
        import transaction
        from ZODB.tests.MinPO import MinPO
        tm1 = transaction.TransactionManager()
        conn = db.open(transaction_manager=tm1)
        r1 = conn.root()
        obj = MinPO('root')
        r1["p"] = obj
        obj = r1["p"]
        obj.child1 = MinPO('child1')
        tm1.get().commit()

        # start a new transaction with a new connection
        tm2 = transaction.TransactionManager()
        cn2 = db.open(transaction_manager=tm2)
        r2 = cn2.root()
        r2["p"]._p_activate()

        self.assertEqual(r1._p_serial, r2._p_serial)

        obj.child2 = MinPO('child2')
        tm1.get().commit()

        # resume the transaction using cn2
        obj = r2["p"]

        # An attempt to access obj.child1 should fail with an RCE
        # below if conn isn't using mvcc, because r2 was read earlier
        # in the transaction and obj was modified by the other
        # transaction.

        obj.child1
        return obj

    def test_conflict_cache_clears_over_time(self):
        import time
        from ZODB.tests.MinPO import MinPO
        storage = self._makeOne()
        storage._conflict_cache_gcevery = 1 # second
        storage._conflict_cache_maxage = 1  # second

        oid = storage.new_oid()
        self._dostore(storage, oid, data=MinPO(5))

        time.sleep(2)

        oid2 = storage.new_oid()
        self._dostore(storage, oid2, data=MinPO(10))

        oid3 = storage.new_oid()
        self._dostore(storage, oid3, data=MinPO(9))

        self.assertEqual(len(storage._conflict_cache), 2)

        time.sleep(2)

        oid4 = storage.new_oid()
        self._dostore(storage, oid4, data=MinPO(11))

        self.assertEqual(len(storage._conflict_cache), 1)

    def test_have_MVCC_ergo_no_ReadConflict(self):
        from ZODB.DB import DB
        from ZODB.tests.MinPO import MinPO
        storage = self._makeOne()
        db = DB(storage)
        ob = self._do_read_conflict(db, True)
        self.assertEquals(ob.__class__, MinPO)
        self.assertEquals(getattr(ob, 'child1', MinPO()).value, 'child1')
        self.failIf(getattr(ob, 'child2', None))

    def test_load_ex_matches_load(self):
        from ZODB.tests.MinPO import MinPO
        storage = self._makeOne()
        oid = storage.new_oid()
        self._dostore(storage, oid, data=MinPO(1))
        loadp, loads = storage.load(oid, 'whatever')
        exp, exs, exv = storage.loadEx(oid, 'whatever')
        self.assertEqual(loadp, exp)
        self.assertEqual(loads, exs)
        self.assertEqual(exv, '')


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TemporaryStorageTests),
        # Note:  we follow the ZODB 'check' pattern here so that the base
        # class tests are picked up.
        unittest.makeSuite(ZODBProtocolTests, 'check'),
    ))
