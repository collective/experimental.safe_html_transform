from zope.interface import implements
from zope.component import getUtility, getMultiAdapter

from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.rule.interfaces import IRuleAction
from plone.contentrules.rule.interfaces import IExecutable

from plone.app.contentrules.actions.copy import CopyAction
from plone.app.contentrules.actions.copy import CopyEditForm

from plone.app.contentrules.rule import Rule

from plone.app.contentrules.tests.base import ContentRulesTestCase

from zope.component.interfaces import IObjectEvent

from Products.PloneTestCase.setup import default_user


class DummyEvent(object):
    implements(IObjectEvent)

    def __init__(self, object):
        self.object = object


class TestCopyAction(ContentRulesTestCase):

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.portal.invokeFactory('Folder', 'target')
        self.login(default_user)
        self.folder.invokeFactory('Document', 'd1')

    def testRegistered(self):
        element = getUtility(IRuleAction, name='plone.actions.Copy')
        self.assertEqual('plone.actions.Copy', element.addview)
        self.assertEqual('edit', element.editview)
        self.assertEqual(None, element.for_)
        self.assertEqual(IObjectEvent, element.event)

    def testInvokeAddView(self):
        element = getUtility(IRuleAction, name='plone.actions.Copy')
        storage = getUtility(IRuleStorage)
        storage[u'foo'] = Rule()
        rule = self.portal.restrictedTraverse('++rule++foo')

        adding = getMultiAdapter((rule, self.portal.REQUEST), name='+action')
        addview = getMultiAdapter((adding, self.portal.REQUEST), name=element.addview)

        addview.createAndAdd(data={'target_folder': '/target', })

        e = rule.actions[0]
        self.assertTrue(isinstance(e, CopyAction))
        self.assertEqual('/target', e.target_folder)

    def testInvokeEditView(self):
        element = getUtility(IRuleAction, name='plone.actions.Copy')
        e = CopyAction()
        editview = getMultiAdapter((e, self.folder.REQUEST), name=element.editview)
        self.assertTrue(isinstance(editview, CopyEditForm))

    def testExecute(self):
        e = CopyAction()
        e.target_folder = '/target'

        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)), IExecutable)
        self.assertEqual(True, ex())

        self.assertTrue('d1' in self.folder.objectIds())
        self.assertTrue('d1' in self.portal.target.objectIds())

    def testExecuteWithError(self):
        e = CopyAction()
        e.target_folder = '/dummy'

        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)), IExecutable)
        self.assertEqual(False, ex())

        self.assertTrue('d1' in self.folder.objectIds())
        self.assertFalse('d1' in self.portal.target.objectIds())

    def testExecuteWithoutPermissionsOnTarget(self):
        self.setRoles(('Member', ))

        e = CopyAction()
        e.target_folder = '/target'

        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)), IExecutable)
        self.assertEqual(True, ex())

        self.assertTrue('d1' in self.folder.objectIds())
        self.assertTrue('d1' in self.portal.target.objectIds())

    def testExecuteWithNamingConflict(self):
        self.setRoles(('Manager', ))
        self.portal.target.invokeFactory('Document', 'd1')
        self.setRoles(('Member', ))

        e = CopyAction()
        e.target_folder = '/target'

        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)), IExecutable)
        self.assertEqual(True, ex())

        self.assertTrue('d1' in self.folder.objectIds())
        self.assertTrue('d1' in self.portal.target.objectIds())
        self.assertTrue('d1.1' in self.portal.target.objectIds())

    def testExecuteWithNamingConflictDoesNotStupidlyAcquireHasKey(self):
        # self.folder is an ATBTreeFolder and so has a has_key. self.folder.target
        # does not. Let's make sure we don't accidentally acquire has_key and use
        # this for the check for unique id.

        self.folder.invokeFactory('Folder', 'target')
        self.folder.target.invokeFactory('Document', 'd1')

        e = CopyAction()
        e.target_folder = '/Members/%s/target' % default_user

        ex = getMultiAdapter((self.folder.target, e, DummyEvent(self.folder.d1)), IExecutable)
        self.assertEqual(True, ex())

        self.assertTrue('d1' in self.folder.objectIds())
        self.assertTrue('d1' in self.folder.target.objectIds())
        self.assertTrue('d1.1' in self.folder.target.objectIds())


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestCopyAction))
    return suite
