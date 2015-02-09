##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import unittest

def faux_connect(self, connection_string):
    setattr(self, '_connected_to', connection_string)


class ConnectionTests(unittest.TestCase):

    def _getTargetClass(self):
        from Shared.DC.ZRDB.Connection import Connection
        Connection.connect = faux_connect
        return Connection

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_connect_on_load(self):
        conn1 = self._makeOne('conn1', '', 'conn string 1')
        conn1.__setstate__(None)
        self.assertEqual(conn1._connected_to, 'conn string 1')

        conn2 = self._makeOne('conn2', '', 'conn string 2')
        conn2.connect_on_load = False
        conn2.__setstate__(None)
        self.failIf(hasattr(conn2, '_connected_to'))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ConnectionTests))
    return suite
