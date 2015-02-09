from Products.Five import fiveconfigure
from Products.Five.zcml import load_config


class PloneFolderLayer:

    @classmethod
    def setUp(cls):
        # load zcml & install the package
        fiveconfigure.debug_mode = True
        from zope import component, annotation
        load_config('meta.zcml', component)
        load_config('configure.zcml', annotation)
        from plone import folder
        load_config('configure.zcml', folder)
        fiveconfigure.debug_mode = False

    @classmethod
    def tearDown(cls):
        pass
