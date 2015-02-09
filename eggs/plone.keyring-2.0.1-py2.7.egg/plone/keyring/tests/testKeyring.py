import types
from unittest import makeSuite
from unittest import TestCase
from unittest import TestSuite
from zope.interface.verify import verifyClass
from plone.keyring.interfaces import IKeyring
from plone.keyring.keyring import Keyring

class KeyringTests(TestCase):
    def testInterface(self):
        verifyClass(IKeyring, Keyring)

    def testConstructionDefaultSize(self):
        ring=Keyring()
        self.assertEqual(len(ring), 5)

    def testConstructionSize(self):
        ring=Keyring(3)
        self.assertEqual(len(ring), 3)

    def testKeyringStartsEmpty(self):
        ring=Keyring()
        self.assertEqual(set(list(ring)), set([None]))

    def testIterate(self):
        ring=Keyring()
        ring.data=[0, 1, 2, 3, 4]
        iterator=ring.__iter__()
        self.failUnless(isinstance(iterator, types.GeneratorType))
        self.assertEqual(list(iterator), [0, 1, 2, 3, 4])

    def testClear(self):
        ring=Keyring()
        ring.data=[0, 1, 2]
        ring.clear()
        self.assertEqual(ring.data, [ None, None, None ])

    def testRotate(self):
        ring=Keyring()
        ring.rotate()
        self.failIf(ring.current is None)
        self.assertEqual(ring.data[1:], [ None, None, None, None])

    def testRotateTwice(self):
        ring=Keyring()
        ring.rotate()
        ring.rotate()
        self.failUnless(ring.data[0] is not None)
        self.failUnless(ring.data[1] is not None)
        self.assertEqual(ring.data[2:], [ None, None, None])

    def testCurrent(self):
        ring=Keyring()
        marker=[]
        ring.data=[marker, 1, 2, 3]
        self.failUnless(ring.current is marker)


def test_suite():
    suite=TestSuite()
    suite.addTest(makeSuite(KeyringTests))
    return suite

