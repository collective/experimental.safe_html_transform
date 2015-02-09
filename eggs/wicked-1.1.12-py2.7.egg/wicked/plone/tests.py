# we want to test each configuration to make sure what we think is
# happening does.
import unittest
from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import ptc, five
from Products.PloneTestCase.layer import ZCML, PloneSite
from wicked.at.tests import wickedtestcase as wtc
from wicked.at.tests import test_cache, test_linking
from wicked.at.tests.wickedtestcase import WickedSite
from wicked.fieldevent import meta
import wicked.plone as here
from Products.PloneTestCase.layer import PloneSite

from Testing import ZopeTestCase

# oh ghost of Tiran forgive me, but type substitution is important
test_klasses = (test_cache.TestLinkCache,
                test_linking.TestDocCreation,
                test_linking.TestWikiLinking,
                test_linking.TestLinkNormalization,
                test_linking.TestRemoteLinking)

ptc.setupPloneSite()

# this manhandles the zcml a bit


from registration import basic_type_regs

class ZCMLLayer(PloneSite):
    @classmethod
    def setUp(cls):
        fiveconfigure.debug_mode = True
        zcml.load_config('all-at.zcml', here)
        fiveconfigure.debug_mode = False

class SelectiveATCT(PloneSite):

    @classmethod
    def setUp(cls):
        app = ZopeTestCase.app()
        plone = app.plone
        for factory in basic_type_regs:
            factory(plone).handle()
        import transaction as txn
        txn.commit()
        ZopeTestCase.close(app)

    @classmethod
    def tearDown(cls):
        """thanks to the zcml load, teardown is not an option"""
        import transaction as txn
        app = ZopeTestCase.app()
        plone = app.plone
        for factory in basic_type_regs:
            factory(plone).handle(unregister=True)
        txn.commit()
        ZopeTestCase.close(app)


def make_wicked_suite(klasses, layer, content_type="Document", field="text"):
    """a factory to spitting out a new test class and new suite for
    these functional tests"""
    suite = unittest.TestSuite()

    for klass in klasses:
        newname = '%s_%s' %(klass.__name__, layer.__name__)
        bases = (klass,)
        newdict = dict(wicked_type=content_type,
                       wicked_field=field,
                       layer=layer,
                       setter='setText')
        newklass = type(newname, bases, newdict)
        new = unittest.makeSuite(newklass)
        suite.addTest(new)
    return suite


def test_suite():
    suites = make_wicked_suite(test_klasses, SelectiveATCT)
    return unittest.TestSuite(suites)


