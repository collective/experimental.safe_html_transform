from zope.component import getMultiAdapter

try:
    from Zope2.App import zcml  # Zope >= 2.13
    zcml  # pyflakes
except ImportError:
    from Products.Five import zcml  # Zope < 2.13
from Products.Five import fiveconfigure
from Testing import ZopeTestCase as ztc

from Products.Archetypes.tests.utils import makeContent
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import PloneSite
from Products.PloneTestCase.layer import onsetup
from Products.PloneTestCase.setup import default_user
from Products.PloneTestCase.setup import default_password

from archetypes.referencebrowserwidget.config import WITH_SAMPLE_TYPES

# setup session
app = ztc.app()
ztc.utils.setupCoreSessions(app)
ztc.close(app)


@onsetup
def setup_sample_types():
    # setup sample types
    if not WITH_SAMPLE_TYPES:
        # if WITH_SAMPLE_TYPES is True the the profile is registered in
        # __init__.py already
        from Products.GenericSetup import EXTENSION, profile_registry
        profile_registry.registerProfile('referencebrowserwidget_sampletypes',
            'ReferenceBrowserWidget Sample Content Types',
            'Extension profile including referencebrowserwidget sample content types',
            'profiles/sample_types',
            'archetypes.referencebrowserwidget',
            EXTENSION)
setup_sample_types()

# install site
ptc.setupPloneSite(extension_profiles=[
    'archetypes.referencebrowserwidget:default',
    'archetypes.referencebrowserwidget:referencebrowserwidget_sampletypes'
    ])

import archetypes.referencebrowserwidget


class MixIn(object):
    """ Mixin for setting up the necessary bits for testing the
        archetypes.referencebrowserwidget
    """
    class layer(PloneSite):
        @classmethod
        def setUp(cls):
            fiveconfigure.debug_mode = True
            zcml.load_config('configure.zcml',
                             archetypes.referencebrowserwidget)
            ptc.installPackage('archetypes.referencebrowserwidget')
            fiveconfigure.debug_mode = False

        @classmethod
        def tearDown(cls):
            pass

    def createDefaultStructure(self):
        if 'layer1' not in self.portal.objectIds():
            self.setRoles(['Manager'])
            makeContent(self.portal, portal_type='Folder', id='layer1')
            self.portal.layer1.setTitle('Layer1')
            self.portal.layer1.reindexObject()
            makeContent(self.portal.layer1, portal_type='Folder', id='layer2')
            self.folder = self.portal.layer1.layer2
            self.folder.setTitle('Layer2')
            self.folder.reindexObject()
            self.setRoles(['Member'])
        return self.portal.layer1.layer2

    def removeDefaultStructure(self):
        if 'layer1' in self.portal.objectIds():
            self.portal._delObject('layer1')


class TestCase(MixIn, ptc.PloneTestCase):
    """ Base TestCase for archetypes.referencebrowserwidget """


class FunctionalTestCase(MixIn, ptc.FunctionalTestCase):
    """ Base FunctionalTestCase for archetypes.referencebrowserwidget """

    basic_auth = '%s:%s' % (default_user, default_password)


class DummySession(dict):

    def set(self, key, value):
        self[key] = value


class DummyObject(object):

    def __init__(self, location):
        self.location = location

    def getPhysicalPath(self):
        return self.location.split('/')


class PopupBaseTestCase(TestCase):

    def afterSetUp(self):
        self.folder = self.createDefaultStructure()
        makeContent(self.folder, portal_type='RefBrowserDemo', id='ref')
        if 'news' not in self.portal.objectIds():
            self.setRoles(['Manager'])
            makeContent(self.portal, portal_type='Folder', id='news')
            self.setRoles(['Member'])
        self.obj = self.folder.ref
        self.obj.reindexObject()
        self.request = self.app.REQUEST
        setattr(self.request, 'SESSION', DummySession())

    def _getPopup(self, obj=None, request=None):
        if obj is None:
            obj = self.obj
        if request is None:
            request = self.request
        popup = getMultiAdapter((obj, request), name='refbrowser_popup')
        popup.update()
        return popup


def normalize(s):
    """ Helper method for integration tests """
    return ' '.join(s.split())
