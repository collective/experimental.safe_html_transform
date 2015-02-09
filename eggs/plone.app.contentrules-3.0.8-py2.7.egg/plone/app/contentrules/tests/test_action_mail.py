# -*- coding: utf-8 -*-
from email import message_from_string
from email.Message import Message
from zope.component import getUtility, getMultiAdapter, getSiteManager
from zope.component.interfaces import IObjectEvent
from zope.interface import implements

from plone.app.contentrules.rule import Rule
from plone.app.contentrules.tests.base import ContentRulesTestCase
from plone.app.contentrules.actions.mail import MailAction, MailEditForm, MailAddForm
from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.rule.interfaces import IRuleAction, IExecutable

from Products.MailHost.interfaces import IMailHost
from Products.MailHost.MailHost import MailHost


class DummyEvent(object):
    implements(IObjectEvent)

    def __init__(self, object):
        self.object = object


class DummyMailHost(MailHost):
    meta_type = 'Dummy Mail Host'

    def __init__(self, id):
        self.id = id
        self.sent = []

    def _send(self, mfrom, mto, messageText, *args, **kw):
        msg = message_from_string(messageText)
        self.sent.append(msg)


class TestMailAction(ContentRulesTestCase):

    def afterSetUp(self):
        self.setRoles(('Manager', ))
        self.portal.invokeFactory('Folder', 'target')
        self.folder.invokeFactory('Document', 'd1',
                                  title='W\xc3\xa4lkommen'.decode('utf-8'))

        users = (
        ('userone', 'User One', 'user@one.com', ('Manager', 'Member')),
        ('usertwo', 'User Two', 'user@two.com', ('Reviewer', 'Member')),
        ('userthree', 'User Three', 'user@three.com', ('Owner', 'Member')),
        ('userfour', 'User Four', 'user@four.com', ('Member', )),
        )
        for id, fname, email, roles in users:
            self.portal.portal_membership.addMember(id, 'secret', roles, [])
            member = self.portal.portal_membership.getMemberById(id)
            member.setMemberProperties({'fullname': fname, 'email': email})

    def testRegistered(self):
        element = getUtility(IRuleAction, name='plone.actions.Mail')
        self.assertEqual('plone.actions.Mail', element.addview)
        self.assertEqual('edit', element.editview)
        self.assertEqual(None, element.for_)

    def testInvokeAddView(self):
        element = getUtility(IRuleAction, name='plone.actions.Mail')
        storage = getUtility(IRuleStorage)
        storage[u'foo'] = Rule()
        rule = self.portal.restrictedTraverse('++rule++foo')

        adding = getMultiAdapter((rule, self.portal.REQUEST), name='+action')
        addview = getMultiAdapter((adding, self.portal.REQUEST),
                                  name=element.addview)
        self.assertTrue(isinstance(addview, MailAddForm))

        addview.createAndAdd(data={'subject': 'My Subject',
                                   'source': 'foo@bar.be',
                                   'recipients': 'foo@bar.be,bar@foo.be',
                                   'message': 'Hey, Oh!'})

        e = rule.actions[0]
        self.assertTrue(isinstance(e, MailAction))
        self.assertEqual('My Subject', e.subject)
        self.assertEqual('foo@bar.be', e.source)
        self.assertEqual('foo@bar.be,bar@foo.be', e.recipients)
        self.assertEqual('Hey, Oh!', e.message)

    def testInvokeEditView(self):
        element = getUtility(IRuleAction, name='plone.actions.Mail')
        e = MailAction()
        editview = getMultiAdapter((e, self.folder.REQUEST),
                                   name=element.editview)
        self.assertTrue(isinstance(editview, MailEditForm))

    def testExecute(self):
        self.loginAsPortalOwner()
        self.portal.portal_membership.getAuthenticatedMember().setProperties(email='currentuser@foobar.com')
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IMailHost)
        dummyMailHost = DummyMailHost('dMailhost')
        sm.registerUtility(dummyMailHost, IMailHost)
        e = MailAction()
        e.source = "$user_email"
        e.recipients = "bar@foo.be, bar@foo.be, $reviewer_emails, $manager_emails, $member_emails"
        e.message = "P\xc3\xa4ge '${title}' created in ${url} !".decode('utf-8')
        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)),
                             IExecutable)
        ex()
        self.assertTrue(isinstance(dummyMailHost.sent[0], Message))

        sent_mails = dict([(mailSent.get('To'), mailSent) for mailSent in dummyMailHost.sent])

        mailSent = sent_mails['bar@foo.be']
        self.assertEqual('text/plain; charset="utf-8"',
                        mailSent.get('Content-Type'))
        self.assertEqual("currentuser@foobar.com", mailSent.get('From'))
        # The output message should be a utf-8 encoded string
        self.assertEqual("P\xc3\xa4ge 'W\xc3\xa4lkommen' created in http://nohost/plone/Members/test_user_1_/d1 !",
                         mailSent.get_payload(decode=True))

        # check interpolation of $reviewer_emails
        self.assertTrue("user@two.com" in sent_mails)

        # check interpolation of $manager_emails
        self.assertTrue("user@one.com" in sent_mails)

        # check interpolation of $member_emails
        self.assertEqual(set(["bar@foo.be", "user@one.com", "user@two.com", "user@three.com", "user@four.com", ]),
                         set(sent_mails.keys()))

    def testExecuteNoSource(self):
        self.loginAsPortalOwner()
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IMailHost)
        dummyMailHost = DummyMailHost('dMailhost')
        sm.registerUtility(dummyMailHost, IMailHost)
        e = MailAction()
        e.recipients = 'bar@foo.be,foo@bar.be'
        e.message = 'Document created !'
        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)),
                             IExecutable)
        # this no longer errors since it breaks usability
        self.assertTrue(ex)
        # and will return False for the unsent message
        self.assertEqual(ex(), False)
        # if we provide a site mail address the message sends correctly
        sm.manage_changeProperties({'email_from_address': 'manager@portal.be', 'email_from_name': 'plone@rulez'})
        ex()
        self.assertTrue(isinstance(dummyMailHost.sent[0], Message))
        mailSent = dummyMailHost.sent[0]
        self.assertEqual('text/plain; charset="utf-8"',
                        mailSent.get('Content-Type'))
        self.assertEqual("bar@foo.be", mailSent.get('To'))
        self.assertEqual('"plone@rulez" <manager@portal.be>',
                         mailSent.get('From'))
        self.assertEqual("Document created !",
                         mailSent.get_payload(decode=True))

    def testExecuteMultiRecipients(self):
        self.loginAsPortalOwner()
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IMailHost)
        dummyMailHost = DummyMailHost('dMailhost')
        sm.registerUtility(dummyMailHost, IMailHost)
        e = MailAction()
        e.source = 'foo@bar.be'
        e.recipients = 'bar@foo.be,foo@bar.be'
        e.message = 'Document created !'
        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)),
                             IExecutable)
        ex()
        self.assertEqual(len(dummyMailHost.sent), 2)
        self.assertTrue(isinstance(dummyMailHost.sent[0], Message))
        mailSent = dummyMailHost.sent[0]
        self.assertEqual('text/plain; charset="utf-8"',
                        mailSent.get('Content-Type'))
        self.assertEqual('bar@foo.be', mailSent.get('To'))
        self.assertEqual('foo@bar.be', mailSent.get('From'))
        self.assertEqual('Document created !', mailSent.get_payload(decode=True))
        mailSent = dummyMailHost.sent[1]
        self.assertEqual('text/plain; charset="utf-8"',
                        mailSent.get('Content-Type'))
        self.assertEqual('foo@bar.be', mailSent.get('To'))
        self.assertEqual('foo@bar.be', mailSent.get('From'))
        self.assertEqual('Document created !', mailSent.get_payload(decode=True))

    def testExecuteExcludeActor(self):
        self.loginAsPortalOwner()
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IMailHost)
        dummyMailHost = DummyMailHost('dMailhost')
        sm.registerUtility(dummyMailHost, IMailHost)
        self.portal.portal_membership.getAuthenticatedMember().setProperties(email='currentuser@foobar.com')
        e = MailAction()
        e.source = "$user_email"
        e.exclude_actor = True
        e.recipients = "bar@foo.be, currentuser@foobar.com"
        e.message = u"A dummy event juste happened !!!!!"
        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)),
                             IExecutable)
        ex()
        self.assertEqual(len(dummyMailHost.sent), 1)

        mailSent = dummyMailHost.sent[0]
        self.assertEqual("bar@foo.be", mailSent.get('To'))

    def testExecuteNoRecipients(self):
        # no recipient
        self.loginAsPortalOwner()
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IMailHost)
        dummyMailHost = DummyMailHost('dMailhost')
        sm.registerUtility(dummyMailHost, IMailHost)
        e = MailAction()
        e.source = 'foo@bar.be'
        e.recipients = ''
        e.message = 'Document created !'
        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)),
                             IExecutable)
        ex()
        self.assertEqual(len(dummyMailHost.sent), 0)

    def testExecuteBadMailHost(self):
        # Our goal is that mailing errors should not cause exceptions
        self.loginAsPortalOwner()
        self.portal.portal_membership.getAuthenticatedMember().setProperties(email='currentuser@foobar.com')
        e = MailAction()
        e.source = "$user_email"
        e.recipients = "bar@foo.be, $reviewer_emails, $manager_emails, $member_emails"
        e.message = u"PÃ¤ge '${title}' created in ${url} !"
        ex = getMultiAdapter((self.folder, e, DummyEvent(self.folder.d1)),
                             IExecutable)
        ex()


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMailAction))
    return suite
