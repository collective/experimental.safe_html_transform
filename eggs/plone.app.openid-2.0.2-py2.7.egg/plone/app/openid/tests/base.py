from OFS.Application import install_package
import plone.openid
from Products.PloneTestCase import PloneTestCase
PloneTestCase.setupPloneSite()

class OpenIdTestCase(PloneTestCase.PloneTestCase):
    def afterSetUp(self):
        # Since Zope 2.10.4 we need to install our package manually
        install_package(self.app, plone.openid, plone.openid.initialize)

    @property
    def pas(self):
        return self.portal.acl_users

    @property
    def pas_info(self):
        return self.pas.restrictedTraverse("@@pas_info")


class OpenIdFunctionalTestCase(PloneTestCase.Functional, OpenIdTestCase):
    pass
