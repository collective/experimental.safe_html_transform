##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for FSFile module. """

import unittest
import Testing

from os.path import join as path_join

from Products.CMFCore.tests.base.dummy import DummyCachingManagerWithPolicy
from Products.CMFCore.tests.base.dummy import DummyCachingManager
from Products.CMFCore.tests.base.testcase import FSDVTest
from Products.CMFCore.tests.base.testcase import RequestTest


class FSFileTests(RequestTest, FSDVTest):

    def setUp(self):
        FSDVTest.setUp(self)
        RequestTest.setUp(self)

    def tearDown(self):
        RequestTest.tearDown(self)
        FSDVTest.tearDown(self)

    def _makeOne( self, id, filename ):

        from Products.CMFCore.FSFile import FSFile
        from Products.CMFCore.FSMetadata import FSMetadata

        full_path = path_join(self.skin_path_name, filename)
        metadata = FSMetadata(full_path)
        metadata.read()
        fsfile_ob = FSFile(id, full_path, properties=metadata.getProperties())

        return fsfile_ob

    def _extractFile( self, filename ):

        path = path_join(self.skin_path_name, filename)
        f = open( path, 'rb' )
        try:
            data = f.read()
        finally:
            f.close()

        return path, data

    def test_ctor( self ):

        path, ref = self._extractFile('test_file.swf')

        file = self._makeOne( 'test_file', 'test_file.swf' )
        file = file.__of__( self.root )

        self.assertEqual( file.get_size(), len( ref ) )
        self.assertEqual( file._readFile(0), ref )

    def test_str( self ):
        path, ref = self._extractFile('test_file.swf')
        file = self._makeOne( 'test_file', 'test_file.swf' )
        file = file.__of__( self.root )
        self.assertEqual( len(str(file)), len( ref ) )

    def test_index_html( self ):

        path, ref = self._extractFile('test_file.swf')

        import os
        from webdav.common import rfc1123_date

        mod_time = os.stat( path )[ 8 ]

        file = self._makeOne( 'test_file', 'test_file.swf' )
        file = file.__of__( self.root )

        data = file.index_html( self.REQUEST, self.RESPONSE )

        self.assertEqual( len( data ), len( ref ) )
        self.assertEqual( data, ref )
        # ICK!  'HTTPResponse.getHeader' doesn't case-flatten the key!
        self.assertEqual( self.RESPONSE.getHeader( 'Content-Length'.lower() )
                        , str(len(ref)) )
        self.assertEqual( self.RESPONSE.getHeader( 'Content-Type'.lower() )
                        , 'application/octet-stream' )
        self.assertEqual( self.RESPONSE.getHeader( 'Last-Modified'.lower() )
                        , rfc1123_date( mod_time ) )

    def test_index_html_with_304( self ):

        path, ref = self._extractFile('test_file.swf')

        import os
        from webdav.common import rfc1123_date

        mod_time = os.stat( path )[ 8 ]

        file = self._makeOne( 'test_file', 'test_file.swf' )
        file = file.__of__( self.root )

        self.REQUEST.environ[ 'IF_MODIFIED_SINCE'
                            ] = '%s;' % rfc1123_date( mod_time+3600 )

        data = file.index_html( self.REQUEST, self.RESPONSE )

        self.assertEqual( data, '' )
        # test that we don't supply a content-length
        self.assertEqual( self.RESPONSE.getHeader('Content-Length'.lower()),
                                               None )
        self.assertEqual( self.RESPONSE.getStatus(), 304 )

    def test_index_html_without_304( self ):

        path, ref = self._extractFile('test_file.swf')

        import os
        from webdav.common import rfc1123_date

        mod_time = os.stat( path )[ 8 ]

        file = self._makeOne( 'test_file', 'test_file.swf' )
        file = file.__of__( self.root )

        self.REQUEST.environ[ 'IF_MODIFIED_SINCE'
                            ] = '%s;' % rfc1123_date( mod_time-3600 )

        data = file.index_html( self.REQUEST, self.RESPONSE )

        self.assertTrue( data, '' )
        self.assertEqual( self.RESPONSE.getStatus(), 200 )

    def test_index_html_with_304_from_cpm( self ):
        self.root.caching_policy_manager = DummyCachingManagerWithPolicy()
        path, ref = self._extractFile('test_file.swf')

        import os
        from webdav.common import rfc1123_date
        from base.dummy import FAKE_ETAG
        
        file = self._makeOne( 'test_file', 'test_file.swf' )
        file = file.__of__( self.root )

        mod_time = os.stat( path )[ 8 ]

        self.REQUEST.environ[ 'IF_MODIFIED_SINCE'
                            ] = '%s;' % rfc1123_date( mod_time )
        self.REQUEST.environ[ 'IF_NONE_MATCH'
                            ] = '%s;' % FAKE_ETAG

        data = file.index_html( self.REQUEST, self.RESPONSE )
        self.assertEqual( len(data), 0 )
        self.assertEqual( self.RESPONSE.getStatus(), 304 )

    def test_index_html_200_with_cpm( self ):
        # should behave the same as without cpm installed
        self.root.caching_policy_manager = DummyCachingManager()
        path, ref = self._extractFile('test_file.swf')

        import os
        from webdav.common import rfc1123_date
        
        file = self._makeOne( 'test_file', 'test_file.swf' )
        file = file.__of__( self.root )

        mod_time = os.stat( path )[ 8 ]

        data = file.index_html( self.REQUEST, self.RESPONSE )

        self.assertEqual( len( data ), len( ref ) )
        self.assertEqual( data, ref )
        # ICK!  'HTTPResponse.getHeader' doesn't case-flatten the key!
        self.assertEqual( self.RESPONSE.getHeader( 'Content-Length'.lower() )
                        , str(len(ref)) )
        self.assertEqual( self.RESPONSE.getHeader( 'Content-Type'.lower() )
                        , 'application/octet-stream' )
        self.assertEqual( self.RESPONSE.getHeader( 'Last-Modified'.lower() )
                        , rfc1123_date( mod_time ) )

    def test_caching( self ):
        self.root.caching_policy_manager = DummyCachingManager()
        original_len = len(self.RESPONSE.headers)
        file = self._makeOne('test_file', 'test_file.swf')
        file = file.__of__(self.root)
        file.index_html(self.REQUEST, self.RESPONSE)
        headers = self.RESPONSE.headers
        self.assertTrue(len(headers) >= original_len + 3)
        self.assertTrue('foo' in headers.keys())
        self.assertTrue('bar' in headers.keys())
        self.assertEqual(headers['test_path'], '/test_file')

    def test_forced_content_type( self ):

        path, ref = self._extractFile('test_file_two.swf')

        import os
        from webdav.common import rfc1123_date

        mod_time = os.stat( path )[ 8 ]

        file = self._makeOne( 'test_file', 'test_file_two.swf' )
        file = file.__of__( self.root )

        data = file.index_html( self.REQUEST, self.RESPONSE )

        self.assertEqual( len( data ), len( ref ) )
        self.assertEqual( data, ref )
        # ICK!  'HTTPResponse.getHeader' doesn't case-flatten the key!
        self.assertEqual( self.RESPONSE.getHeader( 'Content-Length'.lower() )
                        , str(len(ref)) )
        self.assertEqual( self.RESPONSE.getHeader( 'Content-Type'.lower() )
                        , 'application/x-shockwave-flash' )
        self.assertEqual( self.RESPONSE.getHeader( 'Last-Modified'.lower() )
                        , rfc1123_date( mod_time ) )

    def test_utf8charset_detection( self ):
        file_name = 'testUtf8.js'
        file = self._makeOne(file_name, file_name)
        file = file.__of__(self.root)
        file.index_html(self.REQUEST, self.RESPONSE)
        mime = self.RESPONSE.getHeader('content-type')
        self.assertTrue(mime.endswith('; charset=utf-8'))

    def test_unnecessary_invalidation_avoidance(self):
        # See https://bugs.launchpad.net/zope-cmf/+bug/325246
        invalidated = []
        def fake_invalidate(*args, **kw):
            invalidated.append(True)
        file = self._makeOne( 'test_file', 'test_file.swf' )
        file.ZCacheable_invalidate = fake_invalidate

        # First pass: The internal file modification representation
        # equals the filesystem modification time.
        del invalidated[:]
        file._readFile(True)
        self.assertFalse(invalidated)

        del invalidated[:]
        file._parsed = False
        file._updateFromFS()
        self.assertFalse(invalidated)

        # Second pass: Forcing a different internal file modification
        # time onto the instance. Now the file will be invalidated.
        del invalidated[:]
        file._file_mod_time = 0
        file._readFile(True)
        self.assertTrue(invalidated)

        del invalidated[:]
        file._file_mod_time = 0
        file._parsed = False
        file._updateFromFS()
        self.assertTrue(invalidated)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(FSFileTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
