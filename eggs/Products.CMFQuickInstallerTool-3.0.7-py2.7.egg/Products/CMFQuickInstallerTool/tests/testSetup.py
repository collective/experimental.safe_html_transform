#
# Setup tests
#
from plone.app.testing.bbb import PloneTestCase

from Products.CMFQuickInstallerTool.InstalledProduct import InstalledProduct


class TestQuickInstaller(PloneTestCase):

    def afterSetUp(self):
        self.qi = getattr(self.portal, 'portal_quickinstaller', None)

    def testTool(self):
        self.failUnless('portal_quickinstaller' in self.portal.objectIds())

    def testIsNotInstalled(self):
        self.failIf(self.qi.isProductInstalled('CMFQuickInstallerTool'))

    def testIsNotListedAsInstallable(self):
        prods = self.qi.listInstallableProducts()
        prods = [x['id'] for x in prods]
        self.failIf('CMFQuickInstallerTool' in prods)

    def testIsNotListedAsInstalled(self):
        prods = self.qi.listInstalledProducts()
        prods = [x['id'] for x in prods]
        self.failIf('CMFQuickInstallerTool' in prods)


class TestInstalledProduct(PloneTestCase):

    def afterSetUp(self):
        self.qi = getattr(self.portal, 'portal_quickinstaller', None)

    def testSlotsMigration(self):
        # leftslots and rightslots have been class variables ones. Make sure
        # using old instances without these properties doesn't break.

        # New instances should have the properties
        new = InstalledProduct('new')
        self.failUnless(hasattr(new, 'leftslots'))
        self.failUnless(hasattr(new, 'rightslots'))

        # Now emulate an old instance
        old = InstalledProduct('old')
        del(old.leftslots)
        del(old.rightslots)

        # Make sure calling the API will give you no error but silently
        # add the property
        left = old.getLeftSlots()
        self.failUnless(left == [])
        self.failUnless(old.leftslots == [])

        right = old.getRightSlots()
        self.failUnless(right == [])
        self.failUnless(old.rightslots == [])

        slots = old.getSlots()
        self.failUnless(slots == [])
