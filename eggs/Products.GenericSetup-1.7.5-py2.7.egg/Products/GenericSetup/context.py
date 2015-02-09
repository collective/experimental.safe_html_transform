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
""" Various context implementations for export / import of configurations.

Wrappers representing the state of an import / export operation.
"""

import logging
import os
import time
from StringIO import StringIO
from tarfile import DIRTYPE
from tarfile import TarFile
from tarfile import TarInfo

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition import aq_self
from Acquisition import Implicit
from App.class_init import InitializeClass
from DateTime.DateTime import DateTime
from OFS.DTMLDocument import DTMLDocument
from OFS.Folder import Folder
from OFS.Image import File
from OFS.Image import Image
from OFS.Image import Pdata
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from Products.PythonScripts.PythonScript import PythonScript
from zope.interface import implements

from Products.GenericSetup.interfaces import IChunkableExportContext
from Products.GenericSetup.interfaces import IChunkableImportContext
from Products.GenericSetup.interfaces import IExportContext
from Products.GenericSetup.interfaces import IImportContext
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.interfaces import IWriteLogger
from Products.GenericSetup.interfaces import SKIPPED_FILES
from Products.GenericSetup.interfaces import SKIPPED_SUFFIXES
from Products.GenericSetup.permissions import ManagePortal


class Logger:

    implements(IWriteLogger)

    def __init__(self, id, messages):
        """Initialize the logger with a name and an optional level.
        """
        self._id = id
        self._messages = messages
        self._logger = logging.getLogger('GenericSetup.%s' % id)

    def debug(self, msg, *args, **kwargs):
        """Log 'msg % args' with severity 'DEBUG'.
        """
        self.log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Log 'msg % args' with severity 'INFO'.
        """
        self.log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log 'msg % args' with severity 'WARNING'.
        """
        self.log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Log 'msg % args' with severity 'ERROR'.
        """
        self.log(logging.ERROR, msg, *args, **kwargs)

    def exception(self, msg, *args):
        """Convenience method for logging an ERROR with exception information.
        """
        self.error(msg, *args, **{'exc_info': 1})

    def critical(self, msg, *args, **kwargs):
        """Log 'msg % args' with severity 'CRITICAL'.
        """
        self.log(logging.CRITICAL, msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        """Log 'msg % args' with the integer severity 'level'.
        """
        self._messages.append((level, self._id, msg))
        self._logger.log(level, msg, *args, **kwargs)


class SetupEnviron(Implicit):

    """Context for body im- and exporter.
    """

    implements(ISetupEnviron)

    security = ClassSecurityInfo()

    def __init__(self):
        self._should_purge = True

    security.declareProtected(ManagePortal, 'getLogger')
    def getLogger(self, name):
        """Get a logger with the specified name, creating it if necessary.
        """
        return logging.getLogger('GenericSetup.%s' % name)

    security.declareProtected(ManagePortal, 'shouldPurge')
    def shouldPurge(self):
        """When installing, should the existing setup be purged?
        """
        return self._should_purge

InitializeClass(SetupEnviron)


class BaseContext(SetupEnviron):

    security = ClassSecurityInfo()

    def __init__( self, tool, encoding ):

        self._tool = tool
        self._site = aq_parent( aq_inner( tool ) )
        self._loggers = {}
        self._messages = []
        self._encoding = encoding
        self._should_purge = True

    security.declareProtected( ManagePortal, 'getSite' )
    def getSite( self ):

        """ See ISetupContext.
        """
        return aq_self(self._site)

    security.declareProtected( ManagePortal, 'getSetupTool' )
    def getSetupTool( self ):

        """ See ISetupContext.
        """
        return self._tool

    security.declareProtected( ManagePortal, 'getEncoding' )
    def getEncoding( self ):

        """ See ISetupContext.
        """
        return self._encoding

    security.declareProtected( ManagePortal, 'getLogger' )
    def getLogger( self, name ):
        """ See ISetupContext.
        """
        return self._loggers.setdefault(name, Logger(name, self._messages))

    security.declareProtected( ManagePortal, 'listNotes' )
    def listNotes(self):

        """ See ISetupContext.
        """
        return self._messages[:]

    security.declareProtected( ManagePortal, 'clearNotes' )
    def clearNotes(self):

        """ See ISetupContext.
        """
        self._messages[:] = []

InitializeClass(BaseContext)


class DirectoryImportContext( BaseContext ):

    implements(IChunkableImportContext)

    security = ClassSecurityInfo()

    def __init__( self
                , tool
                , profile_path
                , should_purge=False
                , encoding=None
                ):

        BaseContext.__init__( self, tool, encoding )
        self._profile_path = profile_path
        self._should_purge = bool( should_purge )

    security.declareProtected( ManagePortal, 'openDataFile' )
    def openDataFile( self, filename, subdir=None ):

        """ See IImportContext.
        """
        if subdir is None:
            full_path = os.path.join( self._profile_path, filename )
        else:
            full_path = os.path.join( self._profile_path, subdir, filename )

        if not os.path.exists( full_path ):
            return None

        return open( full_path, 'rb' )

    security.declareProtected( ManagePortal, 'readDataFile' )
    def readDataFile( self, filename, subdir=None ):

        """ See IImportContext.
        """
        result = None
        file = self.openDataFile( filename, subdir )
        if file is not None:
            result = file.read()
            file.close()
        return result

    security.declareProtected( ManagePortal, 'getLastModified' )
    def getLastModified( self, path ):

        """ See IImportContext.
        """
        full_path = os.path.join( self._profile_path, path )

        if not os.path.exists( full_path ):
            return None

        return DateTime( os.path.getmtime( full_path ) )

    security.declareProtected( ManagePortal, 'isDirectory' )
    def isDirectory( self, path ):

        """ See IImportContext.
        """
        full_path = os.path.join( self._profile_path, path )

        if not os.path.exists( full_path ):
            return None

        return os.path.isdir( full_path )

    security.declareProtected( ManagePortal, 'listDirectory' )
    def listDirectory(self, path, skip=SKIPPED_FILES,
                      skip_suffixes=SKIPPED_SUFFIXES):

        """ See IImportContext.
        """
        if path is None:
            path = ''

        full_path = os.path.join( self._profile_path, path )

        if not os.path.exists( full_path ) or not os.path.isdir( full_path ):
            return None

        names = []
        for name in os.listdir(full_path):
            if name in skip:
                continue
            if [s for s in skip_suffixes if name.endswith(s)]:
                continue
            names.append(name)

        return names

InitializeClass(DirectoryImportContext)


class DirectoryExportContext( BaseContext ):

    implements(IChunkableExportContext)

    security = ClassSecurityInfo()

    def __init__( self, tool, profile_path, encoding=None ):

        BaseContext.__init__( self, tool, encoding )
        self._profile_path = profile_path

    security.declareProtected( ManagePortal, 'openDataFile' )
    def openDataFile( self, filename, content_type, subdir=None ):

        """ See IChunkableExportContext.
        """
        if subdir is None:
            prefix = self._profile_path
        else:
            prefix = os.path.join( self._profile_path, subdir )

        full_path = os.path.join( prefix, filename )

        if not os.path.exists( prefix ):
            os.makedirs( prefix )

        mode = content_type.startswith( 'text/' ) and 'w' or 'wb'

        return open( full_path, mode )

    security.declareProtected( ManagePortal, 'writeDataFile' )
    def writeDataFile( self, filename, text, content_type, subdir=None ):

        """ See IExportContext.
        """
        if isinstance(text, unicode):
            raise ValueError("Unicode text is not supported, even if it only "
                             "contains ascii. Please encode your data. See "
                             "GS 1.7.0 changes for more")
        file = self.openDataFile( filename, content_type, subdir )
        file.write( text )
        file.close()

InitializeClass(DirectoryExportContext)


class TarballImportContext( BaseContext ):

    implements(IImportContext)

    security = ClassSecurityInfo()

    def __init__( self, tool, archive_bits, encoding=None,
                  should_purge=False ):
        BaseContext.__init__( self, tool, encoding )
        self._archive_stream = StringIO(archive_bits)
        self._archive = TarFile.open( 'foo.bar', 'r:gz'
                                    , self._archive_stream )
        self._should_purge = bool( should_purge )

    def readDataFile( self, filename, subdir=None ):

        """ See IImportContext.
        """
        if subdir is not None:
            filename = '/'.join( ( subdir, filename ) )

        try:
            file = self._archive.extractfile( filename )
        except KeyError:
            return None

        return file.read()

    def getLastModified( self, path ):

        """ See IImportContext.
        """
        info = self._getTarInfo( path )
        return info and DateTime(info.mtime) or None

    def isDirectory( self, path ):

        """ See IImportContext.
        """
        info = self._getTarInfo( path )

        if info is not None:
            return info.isdir()

    def listDirectory(self, path, skip=SKIPPED_FILES,
                      skip_suffixes=SKIPPED_SUFFIXES):

        """ See IImportContext.
        """
        if path is None:  # root is special case:  no leading '/'
            path = ''
        else:
            if not self.isDirectory(path):
                return None

            if path[-1] != '/':
                path = path + '/'

        pfx_len = len(path)

        names = []
        for info in self._archive.getmembers():
            name = info.name.rstrip('/')
            if name == path or not name.startswith(path):
                continue
            name = name[pfx_len:]
            if '/' in name:
                # filter out items in subdirs
                continue
            if name in skip:
                continue
            if [s for s in skip_suffixes if name.endswith(s)]:
                continue
            names.append(name)

        return names

    def shouldPurge( self ):

        """ See IImportContext.
        """
        return self._should_purge

    def _getTarInfo( self, path ):
        if path[-1] == '/':
            path = path[:-1]
        try:
            return self._archive.getmember( path )
        except KeyError:
            pass
        try:
            return self._archive.getmember( path + '/' )
        except KeyError:
            return None

InitializeClass(TarballImportContext)


class TarballExportContext( BaseContext ):

    implements(IExportContext)

    security = ClassSecurityInfo()

    def __init__( self, tool, encoding=None ):

        BaseContext.__init__( self, tool, encoding )

        timestamp = time.gmtime()
        archive_name = ( 'setup_tool-%4d%02d%02d%02d%02d%02d.tar.gz'
                       % timestamp[:6] )

        self._archive_stream = StringIO()
        self._archive_filename = archive_name
        self._archive = TarFile.open( archive_name, 'w:gz'
                                    , self._archive_stream )

    security.declareProtected( ManagePortal, 'writeDataFile' )
    def writeDataFile( self, filename, text, content_type, subdir=None ):

        """ See IExportContext.
        """
        if subdir is not None:
            filename = '/'.join( ( subdir, filename ) )

        parents = filename.split('/')[:-1]
        while parents:
            path = '/'.join(parents) + '/'
            if path not in self._archive.getnames():
                info = TarInfo(path)
                info.type = DIRTYPE
                # tarfile.filemode(0755) == '-rwxr-xr-x'
                info.mode = 0755
                info.mtime = time.time()
                self._archive.addfile(info)
            parents.pop()

        info = TarInfo(filename)
        if isinstance(text, str):
            stream = StringIO(text)
            info.size = len(text)
        elif isinstance(text, unicode):
            raise ValueError("Unicode text is not supported, even if it only "
                             "contains ascii. Please encode your data. See "
                             "GS 1.7.0 changes for more")
        else:
            # Assume text is a an instance of a class like
            # Products.Archetypes.WebDAVSupport.PdataStreamIterator, 
            # as in the case of ATFile
            stream = text.file
            info.size = text.size
        info.mtime = time.time()
        self._archive.addfile( info, stream )

    security.declareProtected( ManagePortal, 'getArchive' )
    def getArchive( self ):

        """ Close the archive, and return it as a big string.
        """
        self._archive.close()
        return self._archive_stream.getvalue()

    security.declareProtected( ManagePortal, 'getArchiveFilename' )
    def getArchiveFilename( self ):

        """ Close the archive, and return it as a big string.
        """
        return self._archive_filename

InitializeClass(TarballExportContext)


class SnapshotExportContext( BaseContext ):

    implements(IExportContext)

    security = ClassSecurityInfo()

    def __init__( self, tool, snapshot_id, encoding=None ):

        BaseContext.__init__( self, tool, encoding )
        self._snapshot_id = snapshot_id

    security.declareProtected( ManagePortal, 'writeDataFile' )
    def writeDataFile( self, filename, text, content_type, subdir=None ):

        """ See IExportContext.
        """
        if subdir is not None:
            filename = '/'.join( ( subdir, filename ) )

        sep = filename.rfind('/')
        if sep != -1:
            subdir = filename[:sep]
            filename = filename[sep+1:]

        if isinstance(text, unicode):
            raise ValueError("Unicode text is not supported, even if it only "
                             "contains ascii. Please encode your data. See "
                             "GS 1.7.0 changes for more")

        folder = self._ensureSnapshotsFolder( subdir )

        # TODO: switch on content_type
        ob = self._createObjectByType( filename, text, content_type )
        folder._setObject( str( filename ), ob ) # No Unicode IDs!

    security.declareProtected( ManagePortal, 'getSnapshotURL' )
    def getSnapshotURL( self ):

        """ See IExportContext.
        """
        return '%s/%s' % ( self._tool.absolute_url(), self._snapshot_id )

    security.declareProtected( ManagePortal, 'getSnapshotFolder' )
    def getSnapshotFolder( self ):

        """ See IExportContext.
        """
        return self._ensureSnapshotsFolder()

    #
    #   Helper methods
    #
    security.declarePrivate( '_createObjectByType' )
    def _createObjectByType( self, name, body, content_type ):

        if isinstance( body, unicode ):
            encoding = self.getEncoding()
            if encoding is None:
                body = body.encode()
            else:
                body = body.encode( encoding )

        if name.endswith('.py'):

            ob = PythonScript( name )
            ob.write( body )

        elif name.endswith('.dtml'):

            ob = DTMLDocument( '', __name__=name )
            ob.munge( body )

        elif content_type in ('text/html', 'text/xml' ):

            ob = ZopePageTemplate( name, body
                                 , content_type=content_type )

        elif content_type[:6]=='image/':

            ob=Image( name, '', body, content_type=content_type )

        else:
            ob=File( name, '', body, content_type=content_type )

        return ob

    security.declarePrivate( '_ensureSnapshotsFolder' )
    def _ensureSnapshotsFolder( self, subdir=None ):

        """ Ensure that the appropriate snapshot folder exists.
        """
        path = [ 'snapshots', self._snapshot_id ]

        if subdir is not None:
            path.extend( subdir.split( '/' ) )

        current = self._tool

        for element in path:

            if element not in current.objectIds():
                # No Unicode IDs!
                current._setObject( str( element ), Folder( element ) )

            current = current._getOb( element )

        return current

InitializeClass(SnapshotExportContext)


class SnapshotImportContext( BaseContext ):

    implements(IImportContext)

    security = ClassSecurityInfo()

    def __init__( self
                , tool
                , snapshot_id
                , should_purge=False
                , encoding=None
                ):

        BaseContext.__init__( self, tool, encoding )
        self._snapshot_id = snapshot_id
        self._encoding = encoding
        self._should_purge = bool( should_purge )

    security.declareProtected( ManagePortal, 'readDataFile' )
    def readDataFile( self, filename, subdir=None ):

        """ See IImportContext.
        """
        if subdir is not None:
            filename = '/'.join( ( subdir, filename ) )

        sep = filename.rfind('/')
        if sep != -1:
            subdir = filename[:sep]
            filename = filename[sep+1:]
        try:
            snapshot = self._getSnapshotFolder( subdir )
            object = snapshot._getOb( filename )
        except ( AttributeError, KeyError ):
            return None

        if isinstance(object, File):
            # OFS File Object have only one way to access the raw
            # data directly, __str__. The code explicitly forbids
            # to store unicode, so str() is safe here
            data = str(object)
        else:
            data = object.read()
        if isinstance(data, unicode):
            data = data.encode('utf-8')
        return data

    security.declareProtected( ManagePortal, 'getLastModified' )
    def getLastModified( self, path ):

        """ See IImportContext.
        """
        try:
            snapshot = self._getSnapshotFolder()
            object = snapshot.restrictedTraverse( path )
        except ( AttributeError, KeyError ):
            return None
        else:
            mtime = getattr(object, '_p_mtime', None)
            if mtime is None:
                # test hook
                mtime = getattr(object, '_faux_mod_time', None)
                if mtime is None:
                    return DateTime()
            return DateTime(mtime)

    security.declareProtected( ManagePortal, 'isDirectory' )
    def isDirectory( self, path ):

        """ See IImportContext.
        """
        try:
            snapshot = self._getSnapshotFolder()
            object = snapshot.restrictedTraverse( str( path ) )
        except ( AttributeError, KeyError ):
            return None
        else:
            folderish = getattr( object, 'isPrincipiaFolderish', False )
            return bool( folderish )

    security.declareProtected( ManagePortal, 'listDirectory' )
    def listDirectory(self, path, skip=(), skip_suffixes=()):

        """ See IImportContext.
        """
        try:
            snapshot = self._getSnapshotFolder()
            subdir = snapshot.restrictedTraverse( path )
        except ( AttributeError, KeyError ):
            return None
        else:
            if not getattr( subdir, 'isPrincipiaFolderish', False ):
                return None

            names = []
            for name in subdir.objectIds():
                if name in skip:
                    continue
                if [s for s in skip_suffixes if name.endswith(s)]:
                    continue
                names.append(name)

            return names

    security.declareProtected( ManagePortal, 'shouldPurge' )
    def shouldPurge( self ):

        """ See IImportContext.
        """
        return self._should_purge

    #
    #   Helper methods
    #
    security.declarePrivate( '_getSnapshotFolder' )
    def _getSnapshotFolder( self, subdir=None ):

        """ Return the appropriate snapshot (sub)folder.
        """
        path = [ 'snapshots', self._snapshot_id ]

        if subdir is not None:
            path.extend( subdir.split( '/' ) )

        return self._tool.restrictedTraverse( path )

InitializeClass(SnapshotImportContext)
