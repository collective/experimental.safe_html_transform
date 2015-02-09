from zope.interface import implements, Interface
from zope.component import getUtility, getMultiAdapter

from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.rule.interfaces import IRuleAction
from plone.contentrules.rule.interfaces import IExecutable

from plone.app.contentrules.actions.notify import NotifyAction
from plone.app.contentrules.actions.notify import NotifyEditForm

from plone.app.contentrules.rule import Rule

from plone.app.contentrules.tests.base import ContentRulesTestCase

from Products.statusmessages import STATUSMESSAGEKEY
from Products.statusmessages.interfaces import IStatusMessage
from Products.statusmessages.adapter import _decodeCookieValue


class DummyEvent(object):
    implements(Interface)


class TestNotifyAction(ContentRulesTestCase):

    def afterSetUp(self):
        self.setRoles(('Manager', ))

    def testRegistered(self):
        element = getUtility(IRuleAction, name='plone.actions.Notify')
        self.assertEqual('plone.actions.Notify', element.addview)
        self.assertEqual('edit', element.editview)
        self.assertEqual(None, element.for_)
        self.assertEqual(None, element.event)

    def testInvokeAddView(self):
        element = getUtility(IRuleAction, name='plone.actions.Notify')
        storage = getUtility(IRuleStorage)
        storage[u'foo'] = Rule()
        rule = self.portal.restrictedTraverse('++rule++foo')

        adding = getMultiAdapter((rule, self.portal.REQUEST), name='+action')
        addview = getMultiAdapter((adding, self.portal.REQUEST), name=element.addview)

        addview.createAndAdd(data={'message': 'Hello world', 'message_type': 'info'})

        e = rule.actions[0]
        self.assertTrue(isinstance(e, NotifyAction))
        self.assertEqual('Hello world', e.message)
        self.assertEqual('info', e.message_type)

    def testInvokeEditView(self):
        element = getUtility(IRuleAction, name='plone.actions.Notify')
        e = NotifyAction()
        editview = getMultiAdapter((e, self.folder.REQUEST), name=element.editview)
        self.assertTrue(isinstance(editview, NotifyEditForm))

    def testExecute(self):
        e = NotifyAction()
        e.message = 'Hello world'
        e.message_type = 'info'

        ex = getMultiAdapter((self.folder, e, DummyEvent()), IExecutable)
        self.assertEqual(True, ex())

        status = IStatusMessage(self.app.REQUEST)
        new_cookies = self.app.REQUEST.RESPONSE.cookies[STATUSMESSAGEKEY]
        messages = _decodeCookieValue(new_cookies['value'])
        self.assertEqual(1, len(messages))
        self.assertEqual('Hello world', messages[0].message)
        self.assertEqual('info', messages[0].type)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestNotifyAction))
    return suite
