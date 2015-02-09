from unittest import makeSuite
from unittest import TestCase
from unittest import TestSuite
from persistent.mapping import PersistentMapping
from zope.interface.verify import verifyClass
from plone.keyring.interfaces import IKeyManager
from plone.keyring.keymanager import KeyManager
from plone.keyring.keyring import Keyring


marker=[]


class KeyManagerTests(TestCase):
    def setUp(self):
        self.mgr=KeyManager()
        del self.mgr[u"_system"]
        self.mgr[u"_system"]=Keyring()
        self.mgr[u"_system"].rotate()
        self.mgr[u"one"]=Keyring()
        self.mgr[u"one"].rotate()
        self.mgr[u"two"]=Keyring()
        self.mgr[u"two"].rotate()


    def testInterface(self):
        verifyClass(IKeyManager, KeyManager)


    def testSystemKeyringCreated(self):
        mgr=KeyManager()
        self.assertEqual(mgr.keys(), [ u"_system" ])
        self.failUnless(mgr[u"_system"].current is not None)


    def testContainerIsPersistent(self):
        mgr=KeyManager()
        self.failUnless(isinstance(mgr.__dict__["_SampleContainer__data"],
                                   PersistentMapping))


    def testClear(self):
        self.mgr.clear()
        self.assertEqual(set(self.mgr[u"_system"]), set([None]))
        self.assertNotEqual(set(self.mgr[u"one"]), set([None]))
        self.assertNotEqual(set(self.mgr[u"two"]), set([None]))


    def testClearGivenRing(self):
        self.mgr.clear(u"one")
        self.assertNotEqual(set(self.mgr[u"_system"]), set([None]))
        self.assertEqual(set(self.mgr[u"one"]), set([None]))
        self.assertNotEqual(set(self.mgr[u"two"]), set([None]))


    def testClearAll(self):
        self.mgr.clear(None)
        self.assertEqual(set(self.mgr[u"_system"]), set([None]))
        self.assertEqual(set(self.mgr[u"one"]), set([None]))
        self.assertEqual(set(self.mgr[u"two"]), set([None]))


    def testClearUnknownRing(self):
        self.assertRaises(KeyError, self.mgr.clear, u"missing")


    def testRotate(self):
        current_sys = self.mgr[u"_system"].current
        current_one = self.mgr[u"one"].current
        current_two = self.mgr[u"two"].current
        self.mgr.rotate()
        self.assertNotEqual(self.mgr[u"_system"].current, current_sys)
        self.assertEqual(self.mgr[u"_system"][1], current_sys)
        self.assertEqual(self.mgr[u"one"].current, current_one)
        self.assertEqual(self.mgr[u"one"][1], None)
        self.assertEqual(self.mgr[u"two"].current, current_two)
        self.assertEqual(self.mgr[u"two"][1], None)


    def testRotateGivenRing(self):
        current_sys = self.mgr[u"_system"].current
        current_one = self.mgr[u"one"].current
        current_two = self.mgr[u"two"].current
        self.mgr.rotate(u"one")
        self.assertEqual(self.mgr[u"_system"].current, current_sys)
        self.assertEqual(self.mgr[u"_system"][1], None)
        self.assertNotEqual(self.mgr[u"one"].current, current_one)
        self.assertEqual(self.mgr[u"one"][1], current_one)
        self.assertEqual(self.mgr[u"two"].current, current_two)
        self.assertEqual(self.mgr[u"two"][1], None)


    def testRotateAll(self):
        current_sys = self.mgr[u"_system"].current
        current_one = self.mgr[u"one"].current
        current_two = self.mgr[u"two"].current
        self.mgr.rotate(None)
        self.assertNotEqual(self.mgr[u"_system"].current, current_sys)
        self.assertEqual(self.mgr[u"_system"][1], current_sys)
        self.assertNotEqual(self.mgr[u"one"].current, current_one)
        self.assertEqual(self.mgr[u"one"][1], current_one)
        self.assertNotEqual(self.mgr[u"two"].current, current_two)
        self.assertEqual(self.mgr[u"two"][1], current_two)


    def testRotateUnknownRing(self):
        self.assertRaises(KeyError, self.mgr.clear, u"missing")


    def testSecret(self):
        self.mgr[u"_system"][0]=marker
        self.failUnless(self.mgr.secret() is marker)

    def testSecretGivenRing(self):
        self.mgr[u"one"][0]=marker
        self.failUnless(self.mgr.secret(u"one") is marker)

    def testSecretUnknownRing(self):
        self.assertRaises(KeyError, self.mgr.secret, u"missing")

def test_suite():
    suite=TestSuite()
    suite.addTest(makeSuite(KeyManagerTests))
    return suite

