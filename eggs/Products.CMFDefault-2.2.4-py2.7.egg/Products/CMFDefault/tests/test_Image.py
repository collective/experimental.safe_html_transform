##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for Image module. """

import unittest
from Testing import ZopeTestCase

from os.path import join as path_join
from cStringIO import StringIO

import transaction
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.User import UnrestrictedUser
from zope.interface.verify import verifyClass
from zope.site.hooks import setSite
from zope.testing.cleanup import cleanUp

from Products.CMFCore.testing import ConformsToContent
from Products.CMFCore.tests.base.dummy import DummyCachingManager
from Products.CMFCore.tests.base.dummy import DummyCachingManagerWithPolicy
from Products.CMFCore.tests.base.dummy import DummySite
from Products.CMFCore.tests.base.dummy import DummyTool
from Products.CMFCore.tests.base.testcase import RequestTest
from Products.CMFDefault import tests
from Products.CMFDefault.testing import FunctionalLayer

from test_File import LMDummyCachingManager

TESTS_HOME = tests.__path__[0]
TEST_JPG = path_join(TESTS_HOME, 'TestImage.jpg')


class TestImageElement(ConformsToContent, unittest.TestCase):

    def _getTargetClass(self):
        from Products.CMFDefault.Image import Image

        return Image

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def setUp(self):
        self.site = DummySite('site')
        self.site._setObject( 'portal_membership', DummyTool() )

    def test_interfaces(self):
        from Products.CMFDefault.interfaces import IFile
        from Products.CMFDefault.interfaces import IImage
        from Products.CMFDefault.interfaces import IMutableFile
        from Products.CMFDefault.interfaces import IMutableImage

        verifyClass(IFile, self._getTargetClass())
        verifyClass(IImage, self._getTargetClass())
        verifyClass(IMutableFile, self._getTargetClass())
        verifyClass(IMutableImage, self._getTargetClass())

    def test_getId_on_old_Image_instance(self):
        image = self.site._setObject('testimage', self._makeOne('testimage'))
        self.assertEqual(image.getId(), 'testimage')
        self.assertEqual(image.id, 'testimage')
        # Mimick old instance when base classes had OFS.Image.Image first
        image.__name__ = 'testimage'
        delattr(image, 'id')
        self.assertEqual(image.getId(), 'testimage')
        self.assertEqual(image.id(), 'testimage')

    def test_EditWithEmptyFile(self):
        # Test handling of empty file uploads
        image = self.site._setObject('testimage', self._makeOne('testimage'))

        testfile = open(TEST_JPG, 'rb')
        image.edit(file=testfile)
        testfile.seek(0,2)
        testfilesize = testfile.tell()
        testfile.close()

        assert image.get_size() == testfilesize

        emptyfile = StringIO()
        image.edit(file=emptyfile)

        assert image.get_size() > 0
        assert image.get_size() == testfilesize

    def test_Image_setFormat(self):
        # Setting the DC.format must also set the content_type property
        image = self._makeOne('testimage', format='image/jpeg')
        self.assertEqual(image.Format(), 'image/jpeg')
        self.assertEqual(image.content_type, 'image/jpeg')
        image.setFormat('image/gif')
        self.assertEqual(image.Format(), 'image/gif')
        self.assertEqual(image.content_type, 'image/gif')

    def test_ImageContentTypeUponConstruction(self):
        # Test the content type after calling the constructor with the
        # file object being passed in (http://www.zope.org/Collectors/CMF/370)
        testfile = open(TEST_JPG, 'rb')
        image = self._makeOne('testimage', file=testfile)
        testfile.close()
        self.assertEqual(image.Format(), 'image/jpeg')
        self.assertEqual(image.content_type, 'image/jpeg')


class TestImageCopyPaste(ZopeTestCase.FunctionalTestCase):

    # Tests related to http://www.zope.org/Collectors/CMF/176
    # Copy/pasting an image (or file) should reset the object's workflow state.

    layer = FunctionalLayer

    def afterSetUp(self):
        setSite(self.app.site)
        newSecurityManager(None, UnrestrictedUser('god', '', ['Manager'], ''))

        self.site = self.app.site
        self.site.invokeFactory('File', id='file')
        self.site.portal_workflow.doActionFor(self.site.file, 'publish')
        self.site.invokeFactory('Image', id='image')
        self.site.portal_workflow.doActionFor(self.site.image, 'publish')
        self.site.invokeFactory('Folder', id='subfolder')
        self.subfolder = self.site.subfolder
        self.workflow = self.site.portal_workflow
        transaction.commit() # Make sure we have _p_jars

    def test_File_CopyPasteResetsWorkflowState(self):
        # Copy/pasting a File should reset wf state to private
        cb = self.site.manage_copyObjects(['file'])
        self.subfolder.manage_pasteObjects(cb)
        review_state = self.workflow.getInfoFor(self.subfolder.file, 'review_state')
        self.assertEqual(review_state, 'private')

    def test_File_CloneResetsWorkflowState(self):
        # Cloning a File should reset wf state to private
        self.subfolder.manage_clone(self.site.file, 'file')
        review_state = self.workflow.getInfoFor(self.subfolder.file, 'review_state')
        self.assertEqual(review_state, 'private')

    def test_File_CutPasteKeepsWorkflowState(self):
        # Cut/pasting a File should keep the wf state
        cb = self.site.manage_cutObjects(['file'])
        self.subfolder.manage_pasteObjects(cb)
        review_state = self.workflow.getInfoFor(self.subfolder.file, 'review_state')
        self.assertEqual(review_state, 'published')

    def test_File_RenameKeepsWorkflowState(self):
        # Renaming a File should keep the wf state
        self.site.manage_renameObjects(['file'], ['file2'])
        review_state = self.workflow.getInfoFor(self.site.file2, 'review_state')
        self.assertEqual(review_state, 'published')

    def test_Image_CopyPasteResetsWorkflowState(self):
        #  Copy/pasting an Image should reset wf state to private
        cb = self.site.manage_copyObjects(['image'])
        self.subfolder.manage_pasteObjects(cb)
        review_state = self.workflow.getInfoFor(self.subfolder.image, 'review_state')
        self.assertEqual(review_state, 'private')

    def test_Image_CloneResetsWorkflowState(self):
        # Cloning an Image should reset wf state to private
        self.subfolder.manage_clone(self.site.image, 'image')
        review_state = self.workflow.getInfoFor(self.subfolder.image, 'review_state')
        self.assertEqual(review_state, 'private')

    def test_Image_CutPasteKeepsWorkflowState(self):
        # Cut/pasting an Image should keep the wf state
        cb = self.site.manage_cutObjects(['image'])
        self.subfolder.manage_pasteObjects(cb)
        review_state = self.workflow.getInfoFor(self.subfolder.image, 'review_state')
        self.assertEqual(review_state, 'published')

    def test_Image_RenameKeepsWorkflowState(self):
        # Renaming an Image should keep the wf state
        self.site.manage_renameObjects(['image'], ['image2'])
        review_state = self.workflow.getInfoFor(self.site.image2, 'review_state')
        self.assertEqual(review_state, 'published')


class TestCaching(RequestTest):

    def _extractFile( self ):

        f = open( TEST_JPG, 'rb' )
        try:
            data = f.read()
        finally:
            f.close()

        return TEST_JPG, data

    def _getTargetClass(self):
        from Products.CMFDefault.Image import Image

        return Image

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def _setupCachingPolicyManager(self, cpm_object):
        self.root.caching_policy_manager = cpm_object

    def tearDown(self):
        cleanUp()
        RequestTest.tearDown(self)

    def test_index_html_with_304_from_cpm( self ):
        self._setupCachingPolicyManager(DummyCachingManagerWithPolicy())
        path, ref = self._extractFile()

        from webdav.common import rfc1123_date
        from Products.CMFCore.tests.base.dummy import FAKE_ETAG

        self.root.file = self._makeOne('test_file', 'test_image.jpg', file=ref)
        file = self.root.file

        mod_time = file.modified()

        self.REQUEST.environ[ 'IF_MODIFIED_SINCE'
                            ] = '%s;' % rfc1123_date( mod_time )
        self.REQUEST.environ[ 'IF_NONE_MATCH'
                            ] = '%s;' % FAKE_ETAG

        data = file.index_html( self.REQUEST, self.RESPONSE )
        self.assertEqual( len(data), 0 )
        self.assertEqual( self.RESPONSE.getStatus(), 304 )

    def test_caching( self ):
        large_data = '0' * 100000
        def fake_response_write(data):
            return
        response_write = self.RESPONSE.write
        self.RESPONSE.write = fake_response_write
        self._setupCachingPolicyManager(DummyCachingManager())
        original_len = len(self.RESPONSE.headers)
        image = self._makeOne('test_image', 'test_image.jpg', file=large_data)
        image = image.__of__(self.root)
        image.index_html(self.REQUEST, self.RESPONSE)
        headers = self.RESPONSE.headers
        self.failUnless(len(headers) >= original_len + 3)
        self.failUnless('foo' in headers.keys())
        self.failUnless('bar' in headers.keys())
        self.assertEqual(headers['test_path'], '/test_image')
        self.RESPONSE.write = response_write

    def test_index_html_200_with_cpm( self ):
        self._setupCachingPolicyManager(DummyCachingManagerWithPolicy())
        path, ref = self._extractFile()

        from webdav.common import rfc1123_date

        file = self._makeOne( 'test_file', 'test_image.jpg', file=ref )
        file = file.__of__( self.root )

        mod_time = file.modified()

        data = file.index_html( self.REQUEST, self.RESPONSE )

        # should behave the same as without cpm
        self.assertEqual( len( data ), len( ref ) )
        self.assertEqual( data, ref )
        # ICK!  'HTTPResponse.getHeader' doesn't case-flatten the key!
        self.assertEqual( self.RESPONSE.getHeader( 'Content-Length'.lower() )
                        , str(len(ref)) )
        self.assertEqual( self.RESPONSE.getHeader( 'Content-Type'.lower() )
                        , 'image/jpeg' )
        self.assertEqual( self.RESPONSE.getHeader( 'Last-Modified'.lower() )
                        , rfc1123_date( mod_time ) )

    def test_index_html_with_304_and_caching( self ):

        # See collector #355
        self._setupCachingPolicyManager(DummyCachingManager())
        original_len = len(self.RESPONSE.headers)
        path, ref = self._extractFile()

        from webdav.common import rfc1123_date

        self.root.image = self._makeOne( 'test_image', 'test_image.gif' )
        image = self.root.image
        transaction.savepoint(optimistic=True)

        mod_time = image.modified()

        self.REQUEST.environ[ 'IF_MODIFIED_SINCE'
                            ] = '%s;' % rfc1123_date( mod_time+1 )

        data = image.index_html( self.REQUEST, self.RESPONSE )

        self.assertEqual( data, '' )
        self.assertEqual( self.RESPONSE.getStatus(), 304 )

        headers = self.RESPONSE.headers
        self.failUnless(len(headers) >= original_len + 3)
        self.failUnless('foo' in headers.keys())
        self.failUnless('bar' in headers.keys())
        self.assertEqual(headers['test_path'], '/test_image')

    def test_caching_policy_headers_are_canonical(self):
        """Ensure that headers set by the caching policy manager trump
        any of the same name that from time to time may be set while 
        rendering the object."""
        path, ref = self._extractFile()

        self._setupCachingPolicyManager(LMDummyCachingManager())

        img = self._makeOne( 'test_image', 'test_image.gif' )
                
        # Cause persistent's modified time record to be set
        self.root.foo = img
        transaction.commit()
        img = self.root.foo
        # end
        
        # index_html in OFS will set Last-modified if ._p_mtime exists
        img.index_html(self.REQUEST, self.RESPONSE)
        
        headers = self.RESPONSE.headers
        self.assertEqual(headers['last-modified'], 
                         "Sun, 06 Nov 1994 08:49:37 GMT")

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestImageElement),
        unittest.makeSuite(TestImageCopyPaste),
        unittest.makeSuite(TestCaching),
        ))

if __name__ == '__main__':
    from Products.CMFCore.testing import run
    run(test_suite())
