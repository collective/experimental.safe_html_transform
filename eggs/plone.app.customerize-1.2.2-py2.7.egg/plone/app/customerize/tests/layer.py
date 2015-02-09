from Products.PloneTestCase.layer import PloneSite
from Testing.ZopeTestCase import installPackage

try:
    from Zope2.App import zcml
    from OFS import metaconfigure
    zcml # pyflakes
    metaconfigure
except ImportError:
    from Products.Five import zcml
    from Products.Five import fiveconfigure as metaconfigure


class PloneCustomerize(PloneSite):

    @classmethod
    def setUp(cls):
        metaconfigure.debug_mode = True
        import plone.app.customerize
        import plone.app.customerize.tests
        zcml.load_config('configure.zcml', plone.app.customerize)
        zcml.load_config('testing.zcml', plone.app.customerize.tests)
        zcml.load_config('duplicate_viewlet.zcml', plone.app.customerize.tests)
        metaconfigure.debug_mode = False
        installPackage('plone.app.customerize', quiet=True)

    @classmethod
    def tearDown(cls):
        pass
