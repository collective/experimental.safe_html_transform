##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Zope Publication Tests

$Id: test_zopepublication.py 114795 2010-07-16 12:21:19Z gary $
"""
import unittest
import sys
from cStringIO import StringIO

from persistent import Persistent
from ZODB.DB import DB
from ZODB.DemoStorage import DemoStorage
import transaction

from zope.interface.verify import verifyClass
from zope.interface import implements, classImplements, implementedBy
from zope.component.interfaces import ComponentLookupError, ISite
from zope.error.interfaces import IErrorReportingUtility
from zope.location import Location
from zope.publisher.base import TestPublication, TestRequest
from zope.publisher.interfaces import IRequest, IPublishTraverse
from zope.security import simplepolicies
from zope.security.management import setSecurityPolicy, queryInteraction
from zope.security.management import endInteraction
from zope.traversing.interfaces import IPhysicallyLocatable
from zope.location.interfaces import ILocation
from zope.testing.cleanup import cleanUp
from zope.site.site import LocalSiteManager

from zope import component
from zope.app.publication.tests import support

from zope.authentication.interfaces import IAuthentication
from zope.authentication.interfaces import IFallbackUnauthenticatedPrincipal
from zope.authentication.interfaces import IUnauthenticatedPrincipal
from zope.security.interfaces import IPrincipal
from zope.principalregistry.principalregistry import principalRegistry
from zope.app.publication.zopepublication import ZopePublication
from zope.site.folder import Folder, rootFolder


class Principal(object):
    implements(IPrincipal)
    def __init__(self, id):
        self.id = id
        self.title = ''
        self.description = ''

class UnauthenticatedPrincipal(Principal):
    implements(IUnauthenticatedPrincipal)

class AuthUtility1(object):

    def authenticate(self, request):
        return None

    def unauthenticatedPrincipal(self):
        return UnauthenticatedPrincipal('test.anonymous')

    def unauthorized(self, id, request):
        pass

    def getPrincipal(self, id):
        return UnauthenticatedPrincipal(id)

class AuthUtility2(AuthUtility1):

    def authenticate(self, request):
        return Principal('test.bob')

    def getPrincipal(self, id):
        return Principal(id)

class AuthUtility3(AuthUtility1):

    def unauthenticatedPrincipal(self):
        return None

class ErrorReportingUtility(object):
    implements(IErrorReportingUtility)

    def __init__(self):
        self.exceptions = []

    def raising(self, info, request=None):
        self.exceptions.append([info, request])

class LocatableObject(Location):

    def foo(self):
        pass

class TestRequest(TestRequest):
    URL='http://test.url'


def addUtility(sitemanager, name, iface, utility, suffix=''):
    """Add a utility to a site manager

    This helper function is useful for tests that need to set up utilities.
    """
    folder_name = (name or (iface.__name__ + 'Utility')) + suffix
    default = sitemanager['default']
    default[folder_name] = utility
    utility = default[folder_name]
    sitemanager.registerUtility(utility, iface, name)
    return utility


class BasePublicationTests(unittest.TestCase):

    def setUp(self):
        from zope.security.management import endInteraction
        endInteraction()
        self.policy = setSecurityPolicy(
            simplepolicies.PermissiveSecurityPolicy
            )
        self.storage = DemoStorage('test_storage')
        self.db = db = DB(self.storage)

        component.provideUtility(principalRegistry, IAuthentication)

        connection = db.open()
        root = connection.root()
        app = getattr(root, ZopePublication.root_name, None)

        if app is None:
            from zope.site.folder import rootFolder
            app = rootFolder()
            root[ZopePublication.root_name] = app
            transaction.commit()

        connection.close()
        self.app = app

        from zope.traversing.namespace import view, resource, etc

        support.provideNamespaceHandler('view', view)
        support.provideNamespaceHandler('resource', resource)
        support.provideNamespaceHandler('etc', etc)

        self.request = TestRequest('/f1/f2')
        self.user = Principal('test.principal')
        self.request.setPrincipal(self.user)
        from zope.interface import Interface
        self.presentation_type = Interface
        self.request._presentation_type = self.presentation_type
        self.object = object()
        self.publication = ZopePublication(self.db)

    def tearDown(self):
        # Close the request, otherwise a Cleanup object will start logging
        # messages from its __del__ method at some inappropriate moment.
        self.request.close()
        cleanUp()


class ZopePublicationErrorHandling(BasePublicationTests):

    def testInterfacesVerify(self):
        for interface in implementedBy(ZopePublication):
            verifyClass(interface, TestPublication)

    def testRetryAllowed(self):
        from ZODB.POSException import ConflictError
        from zope.publisher.interfaces import Retry
        try:
            raise ConflictError
        except:
            self.assertRaises(Retry, self.publication.handleException,
                self.object, self.request, sys.exc_info(), retry_allowed=True)

        try:
            raise Retry(sys.exc_info())
        except:
            self.assertRaises(Retry, self.publication.handleException,
                self.object, self.request, sys.exc_info(), retry_allowed=True)

    def testRetryNotAllowed(self):
        from ZODB.POSException import ConflictError
        from zope.publisher.interfaces import Retry
        try:
            raise ConflictError
        except:
            self.publication.handleException(
                self.object, self.request, sys.exc_info(), retry_allowed=False)
        value = ''.join(self.request.response._result).split()
        self.assertEqual(' '.join(value[:6]),
                         'Traceback (most recent call last): File')
        self.assertEqual(' '.join(value[-8:]),
                         'in testRetryNotAllowed raise ConflictError'
                         ' ConflictError: database conflict error')

        try:
            raise Retry(sys.exc_info())
        except:
            self.publication.handleException(
                self.object, self.request, sys.exc_info(), retry_allowed=False)
        value = ''.join(self.request.response._result).split()
        self.assertEqual(' '.join(value[:6]),
                         'Traceback (most recent call last): File')
        self.assertEqual(' '.join(value[-8:]),
                         'in testRetryNotAllowed raise Retry(sys.exc_info())'
                         ' Retry: database conflict error')

        try:
            raise Retry
        except:
            self.publication.handleException(
                self.object, self.request, sys.exc_info(), retry_allowed=False)
        value = ''.join(self.request.response._result).split()
        self.assertEqual(' '.join(value[:6]),
                         'Traceback (most recent call last): File')
        self.assertEqual(' '.join(value[-6:]),
                         'in testRetryNotAllowed raise Retry'
                         ' Retry: None')

    def testViewOnException(self):
        from zope.interface import Interface
        class E1(Exception):
            pass

        support.setDefaultViewName(E1, 'name',
                                   layer=None,
                                   type=self.presentation_type)
        view_text = 'You had a conflict error'

        def _view(obj, request):
            return lambda: view_text

        component.provideAdapter(_view, (E1, self.presentation_type),
                                 Interface, name='name')

        try:
            raise E1
        except:
            pass
        self.publication.handleException(
            self.object, self.request, sys.exc_info(), retry_allowed=False)
        self.assertEqual(self.request.response._result, view_text)

    def testHandlingSystemErrors(self):

        # Generally, when there is a view for an excepton, we assume
        # it is a user error, not a system error and we don't log it.

        from zope.testing import loggingsupport
        handler = loggingsupport.InstalledHandler('SiteError')

        self.testViewOnException()

        self.assertEqual(
            str(handler),
            'SiteError ERROR\n'
            '  Error while reporting an error to the Error Reporting utility')

        # Here we got a single log record, because we haven't
        # installed an error reporting utility.  That's OK.

        handler.uninstall()
        handler = loggingsupport.InstalledHandler('SiteError')

        # Now, we'll register an exception view that indicates that we
        # have a system error.

        from zope.interface import Interface, implements
        class E2(Exception):
            pass

        support.setDefaultViewName(E2, 'name',
                                   layer=self.presentation_type,
                                   type=self.presentation_type)
        view_text = 'You had a conflict error'

        from zope.browser.interfaces import ISystemErrorView
        class MyView:
            implements(ISystemErrorView)
            def __init__(self, context, request):
                pass

            def isSystemError(self):
                return True

            def __call__(self):
                return view_text

        component.provideAdapter(MyView, (E2, self.presentation_type),
                                 Interface, name='name')

        try:
            raise E2
        except:
            self.publication.handleException(
                self.object, self.request, sys.exc_info(), retry_allowed=False)

        # Now, since the view was a system error view, we should have
        # a log entry for the E2 error (as well as the missing
        # error reporting utility).
        self.assertEqual(
            str(handler),
            'SiteError ERROR\n'
            '  Error while reporting an error to the Error Reporting utility\n'
            'SiteError ERROR\n'
            '  http://test.url'
            )

        handler.uninstall()

    def testNoViewOnClassicClassException(self):
        from zope.interface import Interface
        from types import ClassType
        class ClassicError:
            __metaclass__ = ClassType
        class IClassicError(Interface):
            pass
        classImplements(ClassicError, IClassicError)
        support.setDefaultViewName(IClassicError, 'name',
                                   self.presentation_type)
        view_text = 'You made a classic error ;-)'
        def _view(obj, request):
            return lambda: view_text
        component.provideAdapter(
            _view, (ClassicError, self.presentation_type), Interface,
            name='name')
        try:
            raise ClassicError
        except:
            pass
        self.publication.handleException(
            self.object, self.request, sys.exc_info(), retry_allowed=False)
        # check we don't get the view we registered
        self.failIf(''.join(self.request.response._result) == view_text)
        # check we do actually get something
        self.failIf(''.join(self.request.response._result) == '')

    def testExceptionSideEffects(self):
        from zope.publisher.interfaces import IExceptionSideEffects
        class SideEffects(object):
            implements(IExceptionSideEffects)
            def __init__(self, exception):
                self.exception = exception
            def __call__(self, obj, request, exc_info):
                self.obj = obj
                self.request = request
                self.exception_type = exc_info[0]
                self.exception_from_info = exc_info[1]
        class SideEffectsFactory:
            def __call__(self, exception):
                self.adapter = SideEffects(exception)
                return self.adapter
        factory = SideEffectsFactory()
        from ZODB.POSException import ConflictError
        from zope.interface import Interface
        class IConflictError(Interface):
            pass
        classImplements(ConflictError, IConflictError)
        component.provideAdapter(factory, (IConflictError,),
                                 IExceptionSideEffects)
        exception = ConflictError()
        try:
            raise exception
        except:
            pass
        self.publication.handleException(
            self.object, self.request, sys.exc_info(), retry_allowed=False)
        adapter = factory.adapter
        self.assertEqual(exception, adapter.exception)
        self.assertEqual(exception, adapter.exception_from_info)
        self.assertEqual(ConflictError, adapter.exception_type)
        self.assertEqual(self.object, adapter.obj)
        self.assertEqual(self.request, adapter.request)

    def testExceptionResetsResponse(self):
        from zope.publisher.browser import TestRequest
        request = TestRequest()
        request.response.setHeader('Content-Type', 'application/pdf')
        request.response.setCookie('spam', 'eggs')
        from ZODB.POSException import ConflictError
        try:
            raise ConflictError
        except:
            pass
        self.publication.handleException(
            self.object, request, sys.exc_info(), retry_allowed=False)
        self.assertEqual(request.response.getHeader('Content-Type'),
                         'text/html;charset=utf-8')
        self.assertEqual(request.response._cookies, {})

    def testAbortOrCommitTransaction(self):
        txn = transaction.get()
        try:
            raise Exception
        except:
            pass
        self.publication.handleException(
            self.object, self.request, sys.exc_info(), retry_allowed=False)
        # assert that we get a new transaction
        self.assert_(txn is not transaction.get())

    def testAbortTransactionWithErrorReportingUtility(self):
        # provide our fake error reporting utility
        component.provideUtility(ErrorReportingUtility())

        class FooError(Exception):
            pass

        last_txn_info = self.storage.lastTransaction()
        try:
            raise FooError
        except FooError:
            pass
        self.publication.handleException(
            self.object, self.request, sys.exc_info(), retry_allowed=False)

        # assert that the last transaction is NOT our transaction
        new_txn_info = self.storage.lastTransaction()
        self.assertEqual(last_txn_info, new_txn_info)

        # instead, we expect a message in our logging utility
        error_log = component.getUtility(IErrorReportingUtility)
        self.assertEqual(len(error_log.exceptions), 1)
        error_info, request = error_log.exceptions[0]
        self.assertEqual(error_info[0], FooError)
        self.assert_(isinstance(error_info[1], FooError))
        self.assert_(request is self.request)

    def testLogBeforeAbort(self):
        # If we get an exception, and then (a catastrophe, but one that has
        # been experienced) transaction.abort fails, we really want to know
        # what happened before that abort.
        # (Set up:)
        component.provideUtility(ErrorReportingUtility())
        abort = transaction.abort
        class AbortError(Exception):
            pass
        class AnEarlierError(Exception):
            pass
        def faux_abort():
            raise AbortError
        try:
            raise AnEarlierError()
        except AnEarlierError:
            pass
        transaction.abort = faux_abort
        try:
            # (Test:)
            try:
                self.publication.handleException(
                    self.object, self.request, sys.exc_info(),
                    retry_allowed=False)
            except AbortError:
                pass
            else:
                self.fail('Aborting should have failed')
            # we expect a message in our logging utility
            error_log = component.getUtility(IErrorReportingUtility)
            self.assertEqual(len(error_log.exceptions), 1)
            error_info, request = error_log.exceptions[0]
            self.assertEqual(error_info[0], AnEarlierError)
            self.failUnless(isinstance(error_info[1], AnEarlierError))
            self.failUnless(request is self.request)
        finally:
            # (Tear down:)
            transaction.abort = abort


class ZopePublicationTests(BasePublicationTests):

    def testGlobalAuth(self):
        # Replace the global registry with a stub that doesn't return an
        # unauthenticated principal.
        authentication = AuthUtility3()
        component.provideUtility(authentication, IAuthentication)

        # We need a fallback unauthenticated principal, otherwise we'll get a
        # ComponentLookupError:
        self.assertRaises(ComponentLookupError,
                          self.publication.beforeTraversal, self.request)

        # Let's register an unauthenticated principal instance for the lookup:
        principal = UnauthenticatedPrincipal('fallback')
        component.provideUtility(principal, IFallbackUnauthenticatedPrincipal)

        self.publication.beforeTraversal(self.request)
        self.failUnless(self.request.principal is principal)

    def testTransactionCommitAfterCall(self):
        root = self.db.open().root()
        txn = transaction.get()
        # we just need a change in the database to make the
        # transaction notable in the undo log
        root['foo'] = object()
        last_txn_info = self.storage.lastTransaction()
        self.publication.afterCall(self.request, self.object)
        self.assert_(txn is not transaction.get())
        new_txn_info = self.storage.lastTransaction()
        self.failIfEqual(last_txn_info, new_txn_info)

    def testDoomedTransaction(self):
        # Test that a doomed transaction is aborted without error in afterCall
        root = self.db.open().root()
        txn = transaction.get()
        # we just need a change in the database to make the
        # transaction notable in the undo log
        root['foo'] = object()
        last_txn_info = self.storage.lastTransaction()
        # doom the transaction
        txn.doom()
        self.publication.afterCall(self.request, self.object)
        # assert that we get a new transaction
        self.assert_(txn is not transaction.get())
        new_txn_info = self.storage.lastTransaction()
        # No transaction should be committed
        self.assertEqual(last_txn_info, new_txn_info)

    def testTransactionAnnotation(self):
        from zope.interface import directlyProvides
        from zope.location.traversing import LocationPhysicallyLocatable
        from zope.location.interfaces import ILocation
        from zope.traversing.interfaces import IPhysicallyLocatable
        from zope.traversing.interfaces import IContainmentRoot
        component.provideAdapter(LocationPhysicallyLocatable,
                                 (ILocation,), IPhysicallyLocatable)

        def get_txn_info():
            if hasattr(self.storage, 'iterator'):
                # ZODB 3.9
                txn_id = self.storage.lastTransaction()
                txn = list(self.storage.iterator(txn_id, txn_id))[0]
                txn_info = dict(location=txn.extension['location'],
                                user_name=txn.user,
                                request_type=txn.extension['request_type'])
            else:
                # ZODB 3.8
                txn_info = self.storage.undoInfo()[0]
            return txn_info

        root = self.db.open().root()
        root['foo'] = foo = LocatableObject()
        root['bar'] = bar = LocatableObject()
        bar.__name__ = 'bar'
        foo.__name__ = 'foo'
        bar.__parent__ = foo
        foo.__parent__ = root
        directlyProvides(root, IContainmentRoot)

        from zope.publisher.interfaces import IRequest
        expected_path = "/foo/bar"
        expected_user = "/ " + self.user.id
        expected_request = IRequest.__module__ + '.' + IRequest.getName()

        self.publication.afterCall(self.request, bar)
        txn_info = get_txn_info()
        self.assertEqual(txn_info['location'], expected_path)
        self.assertEqual(txn_info['user_name'], expected_user)
        self.assertEqual(txn_info['request_type'], expected_request)

        # also, assert that we still get the right location when
        # passing an instance method as object.
        self.publication.afterCall(self.request, bar.foo)
        txn_info = get_txn_info()
        self.assertEqual(txn_info['location'], expected_path)

    def testSiteEvents(self):
        from zope.publisher.interfaces import (
            IEndRequestEvent,
            IStartRequestEvent,
            )
        from zope.traversing.interfaces import IBeforeTraverseEvent

        start = []
        set = []
        clear = []

        component.provideHandler(start.append, (IStartRequestEvent,))
        component.provideHandler(set.append, (IBeforeTraverseEvent,))
        component.provideHandler(clear.append, (IEndRequestEvent,))

        ob = object()

        # The request is started at the top of publication, which tries to do
        # auth.  Let's register an unauthenticated principal instance.
        principal = UnauthenticatedPrincipal('fallback')
        component.provideUtility(principal, IFallbackUnauthenticatedPrincipal)
        # Start publication.
        self.publication.beforeTraversal(self.request)
        self.assertEqual(len(start), 1)
        self.assertEqual(start[0].request, self.request)

        # This should fire the BeforeTraverseEvent.
        self.publication.callTraversalHooks(self.request, ob)

        self.assertEqual(len(set), 1)
        self.assertEqual(len(clear), 0)
        self.assertEqual(set[0].object, ob)

        ob2 = object()

        # This should fire the EndRequestEvent
        self.publication.endRequest(self.request, ob2)

        self.assertEqual(len(start), 1)
        self.assertEqual(len(set), 1)
        self.assertEqual(len(clear), 1)
        self.assertEqual(clear[0].object, ob2)

    def testConnectionAnnotation(self):
        """The request is annotated with the connection to the main ZODB.
        """
        self.assertRaises(
            KeyError,
            lambda: self.request.annotations['ZODB.interfaces.IConnection'])

        app = self.publication.getApplication(self.request)
        conn = self.request.annotations['ZODB.interfaces.IConnection']
        self.assertEqual(conn.db(), self.db)


class AuthZopePublicationTests(BasePublicationTests):

    def setUp(self):
        super(AuthZopePublicationTests, self).setUp()
        principalRegistry.defineDefaultPrincipal('anonymous', '')

        root = self.db.open().root()
        app = root[ZopePublication.root_name]
        app['f1'] = rootFolder()
        f1 = app['f1']
        f1['f2'] = Folder()
        if not ISite.providedBy(f1):
            f1.setSiteManager(LocalSiteManager(f1))
        sm1 = f1.getSiteManager()
        addUtility(sm1, '', IAuthentication, AuthUtility1())

        f2 = f1['f2']
        if not ISite.providedBy(f2):
            f2.setSiteManager(LocalSiteManager(f2))
        sm2 = f2.getSiteManager()
        addUtility(sm2, '', IAuthentication, AuthUtility2())
        transaction.commit()

        from zope.container.interfaces import ISimpleReadContainer
        from zope.container.traversal import ContainerTraverser

        component.provideAdapter(ContainerTraverser,
                                 (ISimpleReadContainer, IRequest),
                                 IPublishTraverse, name='')

        from zope.site.interfaces import IFolder
        from zope.security.checker import defineChecker, InterfaceChecker
        defineChecker(Folder, InterfaceChecker(IFolder))

    def testPlacefulAuth(self):
        self.publication.beforeTraversal(self.request)
        self.assertEqual(list(queryInteraction().participations),
                         [self.request])
        self.assertEqual(self.request.principal.id, 'anonymous')
        root = self.publication.getApplication(self.request)
        self.publication.callTraversalHooks(self.request, root)
        self.assertEqual(self.request.principal.id, 'anonymous')
        ob = self.publication.traverseName(self.request, root, 'f1')
        self.publication.callTraversalHooks(self.request, ob)
        self.assertEqual(self.request.principal.id, 'test.anonymous')
        ob = self.publication.traverseName(self.request, ob, 'f2')
        self.publication.afterTraversal(self.request, ob)
        self.assertEqual(self.request.principal.id, 'test.bob')
        self.assertEqual(list(queryInteraction().participations),
                         [self.request])
        self.publication.endRequest(self.request, ob)
        self.assertEqual(queryInteraction(), None)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ZopePublicationTests),
        unittest.makeSuite(AuthZopePublicationTests),
        unittest.makeSuite(ZopePublicationErrorHandling),
        ))

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
