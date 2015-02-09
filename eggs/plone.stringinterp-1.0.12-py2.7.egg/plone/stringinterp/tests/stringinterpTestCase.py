
# Import the base test case classes
from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase
from Products.Five.testbrowser import Browser
from Products.Five import fiveconfigure
from Products.Five import zcml
from Products.PloneTestCase.layer import onsetup
import plone.stringinterp


class Session(dict):
    def set(self, key, value):
        self[key] = value

@onsetup
def setup_product():
    fiveconfigure.debug_mode = True
    zcml.load_config('configure.zcml', plone.stringinterp)
    fiveconfigure.debug_mode = False

setup_product()
PloneTestCase.setupPloneSite()

class TestCase(PloneTestCase.PloneTestCase):
    def _setup(self):
        PloneTestCase.PloneTestCase._setup(self)
        self.app.REQUEST['SESSION'] = Session()

class FunctionalTestCase(PloneTestCase.FunctionalTestCase):

    def _setup(self):
        PloneTestCase.FunctionalTestCase._setup(self)
        self.app.REQUEST['SESSION'] = Session()
        self.browser = Browser()
        self.app.acl_users.userFolderAddUser('root', 'secret', ['Manager'], [])
        self.browser.addHeader('Authorization', 'Basic root:secret')
        self.portal_url = 'http://nohost/plone'
