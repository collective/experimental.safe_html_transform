from Testing import ZopeTestCase

# BBB for Zope 2.12
try:
    from Zope2.App import zcml
except ImportError:
    from Products.Five import zcml

import plone.session
import plone.session.tests
from plone.session.plugins.session import SessionPlugin

from OFS.Folder import Folder


class FakePAS(Folder):
    plugins = None

    def updateCredentials(self, request, response, userid, password):
        self.credentials=(userid, password)

    def _verifyUser(self, plugin, user_id=None, login=None):
        assert user_id is None
        if login=='our_user':
            return dict(id=login, login=login, pluginid="session")
        return None


class PloneSessionTestCase(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        zcml.load_config('meta.zcml', plone.session)
        zcml.load_config('configure.zcml', plone.session)
        zcml.load_config('configure.zcml', plone.session.tests)
        self.folder._setObject("pas", FakePAS("pas"))
        self.folder.pas._setObject("session", SessionPlugin("session"))


class FunctionalPloneSessionTestCase(ZopeTestCase.Functional, PloneSessionTestCase):
    pass
