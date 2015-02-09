from Testing.ZopeTestCase.layer import ZopeLite
from zope.site.hooks import setHooks
from zope.testing.cleanup import cleanUp

# BBB for Zope 2.12
try:
    from Zope2.App import zcml
except ImportError:
    from Products.Five import zcml


class UidEventZCMLLayer(ZopeLite):

    @classmethod
    def testSetUp(cls):
        import Products

        zcml.load_config('meta.zcml', Products.Five)
        zcml.load_config('event.zcml', Products.Five)
        zcml.load_config('event.zcml', Products.CMFUid)
        setHooks()

    @classmethod
    def testTearDown(cls):
        cleanUp()
