from unittest import defaultTestLoader
from plone.app.folder.tests.base import IntegrationTestCase
from plone.app.folder.tests.layer import IntegrationLayer


class UnorderedOrderingTests(IntegrationTestCase):
    """ tests regarding order-support for folders with unordered ordering """

    layer = IntegrationLayer

    def afterSetUp(self):
        self.setRoles(['Manager'])

    def create(self):
        container = self.portal[self.portal.invokeFactory('Folder', 'foo')]
        container.setOrdering('unordered')
        container.invokeFactory('Document', id='o1')
        container.invokeFactory('Document', id='o2')
        return container

    def testNotifyAdded(self):
        container = self.create()
        self.assertEqual(set(container.objectIds()), set(['o1', 'o2']))
        container.invokeFactory('Document', id='o3')
        self.assertEqual(set(container.objectIds()), set(['o1', 'o2', 'o3']))

    def testNotifyRemoved(self):
        container = self.create()
        self.assertEqual(set(container.objectIds()), set(['o1', 'o2']))
        container.manage_delObjects('o2')
        self.assertEqual(set(container.objectIds()), set(['o1']))

    def testGetObjectPosition(self):
        container = self.create()
        self.assertEqual(container.getObjectPosition('o1'), None)
        self.assertEqual(container.getObjectPosition('o2'), None)


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
