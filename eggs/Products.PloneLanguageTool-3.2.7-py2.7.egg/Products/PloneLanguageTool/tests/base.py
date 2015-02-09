from Products.CMFTestCase.ctc import CMFTestCase
from Products.CMFTestCase.ctc import Functional
from Products.CMFTestCase.ctc import installProduct
from Products.CMFTestCase.ctc import setupCMFSite
from Products.CMFTestCase.layer import onsetup

# BBB Zope 2.12
try:
    from Zope2.App import zcml
except ImportError:
    from Products.Five import zcml

# Setup a CMF site
installProduct('PloneLanguageTool')
installProduct('SiteAccess')

setupCMFSite(
    extension_profiles=['Products.PloneLanguageTool:PloneLanguageTool'])


def extraZCML():
    # XXX: Why isn't this loaded as part of site.zcml?
    import plone.i18n.locales
    zcml.load_config('configure.zcml', plone.i18n.locales)

onsetup(extraZCML)()


class TestCase(CMFTestCase):
    """Simple test case
    """

class FunctionalTestCase(Functional, TestCase):
    """Simple test case for functional tests
    """
