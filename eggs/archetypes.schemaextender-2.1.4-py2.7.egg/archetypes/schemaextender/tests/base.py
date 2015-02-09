from Products.PloneTestCase.ptc import setupPloneSite, FunctionalTestCase
from Products.PloneTestCase.layer import PloneSite

# BBB Zope 2.12
try:
    from OFS import metaconfigure
    from Zope2.App.zcml import load_config
except ImportError:
    from Products.Five import fiveconfigure as metaconfigure
    from Products.Five.zcml import load_config


setupPloneSite()


class TestCase(FunctionalTestCase):

    class layer(PloneSite):

        @classmethod
        def setUp(cls):
            metaconfigure.debug_mode = True
            from archetypes import schemaextender
            load_config('configure.zcml', schemaextender)
            metaconfigure.debug_mode = False

        @classmethod
        def tearDown(cls):
            pass

    def clearSchemaCache(self):
        attr = '__archetypes_schemaextender_cache'
        if hasattr(self.portal.REQUEST, attr):
            delattr(self.portal.REQUEST, attr)
