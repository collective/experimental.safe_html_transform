##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test the unique id annotation.

$Id: test_uidannotation.py 110665 2010-04-08 16:12:03Z tseaver $
"""

import unittest
import Testing

import transaction
from AccessControl.SecurityManagement import newSecurityManager
from Acquisition import Implicit
from OFS.Folder import Folder
from zope.component import getSiteManager
from zope.component import getUtility
from zope.interface import implements
from zope.interface.verify import verifyClass

from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.tests.base.dummy import DummyContent
from Products.CMFCore.tests.base.testcase import SecurityTest
from Products.CMFCore.tests.test_PortalFolder import _AllowedUser
from Products.CMFCore.tests.test_PortalFolder import _SensitiveSecurityPolicy
from Products.CMFUid.interfaces import IUniqueIdAnnotationManagement
from Products.CMFUid.interfaces import IUniqueIdHandler
from Products.CMFUid.interfaces import UniqueIdError
from Products.CMFUid.testing import UidEventZCMLLayer

UID_ATTRNAME = 'cmf_uid'


class TheClass(Folder):

    implements(IContentish)


class DummyUniqueIdHandlerTool(Implicit):

    implements(IUniqueIdHandler)

    def __init__(self):
        self.counter = 0

    def register(self, ob):

        uid_assigner = getUtility(IUniqueIdAnnotationManagement)
        annotation = uid_assigner(ob, UID_ATTRNAME)
        annotation.setUid( self.counter )
        self.counter += 1

    def unregister(self, ob):

        try:
           delattr(ob, UID_ATTRNAME)
        except AttributeError:
           raise UniqueIdError


class UniqueIdAnnotationToolTests(SecurityTest):

    layer = UidEventZCMLLayer

    def _getTargetClass(self):
        from Products.CMFUid.UniqueIdAnnotationTool \
                import UniqueIdAnnotationTool

        return UniqueIdAnnotationTool

    def setUp(self):
        SecurityTest.setUp(self)
        self.root._setObject('portal_uidannotation', self._getTargetClass()())
        self.root._setObject('portal_uidhandler', DummyUniqueIdHandlerTool())

        sm = getSiteManager()
        sm.registerUtility( self.root.portal_uidannotation
                          , IUniqueIdAnnotationManagement
                          )

        self.root._setObject('dummy', DummyContent(id='dummy'))
        self.root._setObject('site', Folder('site'))

        transaction.savepoint(optimistic=True)

    def _initPolicyAndUser( self
                          , a_lambda=None
                          , v_lambda=None
                          , c_lambda=None
                          ):
        from AccessControl import SecurityManager

        def _promiscuous( *args, **kw ):
            return 1

        if a_lambda is None:
            a_lambda = _promiscuous

        if v_lambda is None:
            v_lambda = _promiscuous

        if c_lambda is None:
            c_lambda = _promiscuous

        scp = _SensitiveSecurityPolicy( v_lambda, c_lambda )
        SecurityManager.setSecurityPolicy( scp )
        newSecurityManager( None
                          , _AllowedUser(a_lambda).__of__(self.app.acl_users))

    def test_interfaces(self):
        from Products.CMFUid.interfaces import IUniqueIdAnnotation
        from Products.CMFUid.interfaces import IUniqueIdAnnotationManagement
        from Products.CMFUid.UniqueIdAnnotationTool \
                import UniqueIdAnnotation

        verifyClass(IUniqueIdAnnotationManagement, self._getTargetClass())
        verifyClass(IUniqueIdAnnotation, UniqueIdAnnotation)

    def test_setAndGetUid(self):
        dummy = self.root.dummy
        annotation = self.root.portal_uidannotation(dummy, UID_ATTRNAME)

        self.assertEqual(annotation(), None)
        annotation.setUid(13)
        self.assertEqual(annotation(), 13)

    # copy/rename/add events: Just to remember
    #
    # add/import obj:
    #   obj.manage_afterAdd(obj, obj, folder)
    #
    # move/rename obj:
    #   obj.manage_beforeDelete(obj, obj, source_folder)
    #   obj.manage_afterAdd(obj_at_target, obj_at_target, target_folder)
    #
    # copy and paste (clone) obj:
    #   obj.manage_afterAdd(obj_at_target, obj_at_target, target_folder)
    #   obj.manage_afterClone(obj_at_target, obj_at_target)

    def test_simulateItemAddAssigningUid(self):
        # an annotated object is set in place
        dummy = DummyContent(id='dummycontent')
        self.root.portal_uidannotation.assign_on_add = True
        self.root._setObject('dummycontent', dummy)

        annotation = getattr(dummy, UID_ATTRNAME, None)

        self.failUnless(annotation is not None)
    
    def test_simulateItemAddRemovingUid(self):
        # an annotated object is set in place
        dummy = DummyContent(id='dummycontent')
        annotation = self.root.portal_uidannotation(dummy, UID_ATTRNAME)
        self.root._setObject('dummycontent', dummy)

        self.assertRaises(AttributeError, getattr, dummy, UID_ATTRNAME)

    def test_simulateItemAddAssignsNewUid(self):
        # an annotated object is set in place
        dummy = DummyContent(id='dummycontent')
        annotation = self.root.portal_uidannotation(dummy, UID_ATTRNAME)
        self.root.portal_uidannotation.assign_on_add = True
        self.root._setObject('dummycontent', dummy)

        self.failIf( getattr(dummy, UID_ATTRNAME)()==annotation() )

    def test_simulateItemAddDoesNotTouchUid(self):
        # an annotated object is set in place
        dummy = DummyContent(id='dummycontent')
        annotation = self.root.portal_uidannotation(dummy, UID_ATTRNAME)
        self.root.portal_uidannotation.remove_on_add = False
        self.root._setObject('dummycontent', dummy)

        self.assertEqual(getattr(dummy, UID_ATTRNAME), annotation)

    def test_simulateItemRename(self):
        # an object is set in place, annotated and then renamed
        self._initPolicyAndUser() # allow copy/paste operations
        dummy = TheClass('dummy')
        site = self.root.site
        site._setObject('dummy', dummy)
        annotation = self.root.portal_uidannotation(dummy, UID_ATTRNAME)

        transaction.savepoint(optimistic=True)

        site.manage_renameObject(id='dummy', new_id='dummy2')
        new_annotation = getattr(site.dummy2, UID_ATTRNAME)
        self.assertEqual(annotation(), new_annotation())

    def test_simulateItemCloneRemovingUid1(self):
        # an object is set in place, annotated and then copied
        self._initPolicyAndUser() # allow copy/paste operations
        dummy = TheClass('dummy')
        site = self.root.site
        site._setObject('dummy', dummy)
        annotation = self.root.portal_uidannotation(dummy, UID_ATTRNAME)
        self.root._setObject('folder1', Folder('folder1'))

        transaction.savepoint(optimistic=True)
        cookie = site.manage_copyObjects(ids=['dummy'])
        self.root.folder1.manage_pasteObjects( cookie )

        self.assertRaises(AttributeError, getattr, self.root.folder1.dummy, UID_ATTRNAME)

    def test_simulateItemCloneRemovingUid2(self):
        # an object is set in place, annotated and then copied
        self._initPolicyAndUser() # allow copy/paste operations
        dummy = TheClass('dummy')
        site = self.root.site
        site._setObject('dummy', dummy)
        annotation = self.root.portal_uidannotation(dummy, UID_ATTRNAME)
        self.root.portal_uidannotation.remove_on_add = False
        self.root._setObject('folder1', Folder('folder1'))

        transaction.savepoint(optimistic=True)
        cookie = site.manage_copyObjects(ids=['dummy'])
        self.root.folder1.manage_pasteObjects( cookie )

        self.assertRaises(AttributeError, getattr, self.root.folder1.dummy, UID_ATTRNAME)

    def test_simulateItemCloneDoesNotTouchUid(self):
        # an object is set in place, annotated, and then copied
        self._initPolicyAndUser() # allow copy/paste operations
        dummy = TheClass('dummy')
        site = self.root.site
        site._setObject('dummy', dummy)
        annotation = self.root.portal_uidannotation(dummy, UID_ATTRNAME)
        self.root.portal_uidannotation.remove_on_clone = False
        self.root._setObject('folder1', Folder('folder1'))

        transaction.savepoint(optimistic=True)
        cookie = site.manage_copyObjects(ids=['dummy'])
        self.root.folder1.manage_pasteObjects( cookie )
        new_annotation = getattr(self.root.folder1.dummy, UID_ATTRNAME)

        self.assertEqual(annotation(), new_annotation() )

    def test_simulateItemCloneAssignsNewUid(self):
        # an object is set in place, annotated, and then copied
        self._initPolicyAndUser() # allow copy/paste operations
        dummy = TheClass('dummy')
        site = self.root.site
        site._setObject('dummy', dummy)
        annotation = self.root.portal_uidannotation(dummy, UID_ATTRNAME)
        self.root.portal_uidannotation.assign_on_clone = True
        self.root._setObject('folder1', Folder('folder1'))

        transaction.savepoint(optimistic=True)
        cookie = site.manage_copyObjects(ids=['dummy'])
        self.root.folder1.manage_pasteObjects( cookie )
        new_annotation = getattr(self.root.folder1.dummy, UID_ATTRNAME)

        self.failIf( annotation() == new_annotation() )

    def test_simulateNestedFolderCloneRemovingUid1(self):
        self.root.site._setObject( 'foo', Folder(id='foo') )
        self.root.site._setObject( 'foo2', Folder(id='foo2') )
        foo = self.root.site.foo
        foo._setObject( 'sub1', Folder(id='sub1') )
        foo.sub1._setObject( 'sub2', Folder(id='sub2') )
        foo.sub1.sub2._setObject( 'baz', DummyContent(id='baz', catalog=1) )
        baz = foo.sub1.sub2.baz
        annotation = self.root.portal_uidannotation(baz, UID_ATTRNAME)
        self.assertEqual( getattr(baz, UID_ATTRNAME), annotation )

        transaction.savepoint(optimistic=True)
        cookie = self.root.site.manage_copyObjects(ids='foo')
        self.root.site.foo2.manage_pasteObjects(cookie)

        self.assertRaises(AttributeError, getattr, self.root.site.foo2.foo.sub1.sub2.baz, UID_ATTRNAME)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(UniqueIdAnnotationToolTests),
        ))

if __name__ == '__main__':
    from Products.CMFCore.testing import run
    run(test_suite())
