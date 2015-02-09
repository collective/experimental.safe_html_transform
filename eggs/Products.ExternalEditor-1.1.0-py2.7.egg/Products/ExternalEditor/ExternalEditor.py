##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""$Id: ExternalEditor.py 118662 2010-12-01 16:00:28Z tiazma $
"""

# Zope External Editor Product by Casey Duncan

from string import join # For Zope 2.3 compatibility
import types
import urllib
from Acquisition import aq_inner, aq_base, aq_parent, Implicit
try:
    from App.class_init import InitializeClass
except ImportError:
    from App.class_init import default__class_init__ as InitializeClass
from App.Common import rfc1123_date
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityInfo import ClassSecurityInfo
from OFS import Image
try:
    from webdav.Lockable import wl_isLocked
except ImportError:
    # webdav module not available
    def wl_isLocked(ob):
        return 0

from ZPublisher.Iterators import IStreamIterator
from zope.interface import implements, Interface
HAVE_Z3_IFACE = issubclass(IStreamIterator, Interface)

ExternalEditorPermission = 'Use external editor'

_callbacks = []

class PDataStreamIterator:
    if HAVE_Z3_IFACE:
        implements(IStreamIterator)
    else:
        __implements__ = IStreamIterator

    def __init__(self, data):
        self.data = data

    def __iter__(self):
        return self

    def next(self):
        if self.data is None:
            raise StopIteration
        data = self.data.data
        self.data = self.data.next
        return data

def registerCallback(cb):
    """Register a callback to be called by the External Editor when
    it's about to be finished with collecting metadata for the
    to-be-edited file to allow actions to be taken, like for example
    inserting more metadata headers or enabling response compression
    or anything.
    """
    _callbacks.append(cb)

def applyCallbacks(ob, metadata, request, response):
    """Apply the registered callbacks in the order they were
    registered. The callbacks are free to perform any operation,
    including appending new metadata attributes and setting response
    headers.
    """
    for cb in _callbacks:
        cb(ob, metadata, request, response)

class ExternalEditor(Implicit):
    """Create a response that encapsulates the data needed by the
       ZopeEdit helper application
    """

    security = ClassSecurityInfo()
    security.declareObjectProtected(ExternalEditorPermission)

    def __before_publishing_traverse__(self, self2, request):
        path = request['TraversalRequestNameStack']
        if path:
            target = path[-1]
            if target.endswith('.zem'):
                # Remove extension added by EditLink()
                # so we can traverse to the target in Zope
                target = target[:-4]
            request.set('target', target)
            path[:] = []
        else:
            request.set('target', None)

    def index_html(self, REQUEST, RESPONSE, path=None):
        """Publish the object to the external editor helper app"""

        security = getSecurityManager()
        if path is None:
            parent = self.aq_parent
            try:
                ob = parent[REQUEST['target']] # Try getitem
            except KeyError:
                ob = getattr(parent, REQUEST['target']) # Try getattr
            except AttributeError:
                # Handle objects that are methods in ZClasses
                ob = parent.propertysheets.methods[REQUEST['target']]
        else:
            ob = self.restrictedTraverse( path )

        r = []
        r.append('url:%s' % ob.absolute_url())
        r.append('meta_type:%s' % ob.meta_type)

        title = getattr(aq_base(ob), 'title', None)
        if title is not None:
            if callable(title):
                title = title()
            if isinstance(title, types.UnicodeType):
                title = unicode.encode(title, 'utf-8')
            r.append('title:%s' % title)

        if hasattr(aq_base(ob), 'content_type'):
            if callable(ob.content_type):
                r.append('content_type:%s' % ob.content_type())
            else:
                r.append('content_type:%s' % ob.content_type)

        if REQUEST._auth:
            if REQUEST._auth[-1] == '\n':
                auth = REQUEST._auth[:-1]
            else:
                auth = REQUEST._auth

            r.append('auth:%s' % auth)

        r.append('cookie:%s' % REQUEST.environ.get('HTTP_COOKIE',''))

        if wl_isLocked(ob):
            # Object is locked, send down the lock token
            # owned by this user (if any)
            user_id = security.getUser().getId()
            for lock in ob.wl_lockValues():
                if not lock.isValid():
                    continue # Skip invalid/expired locks
                creator = lock.getCreator()
                if creator and creator[1] == user_id:
                    # Found a lock for this user, so send it
                    r.append('lock-token:%s' % lock.getLockToken())
                    if REQUEST.get('borrow_lock'):
                        r.append('borrow_lock:1')
                    break

        # Apply any extra callbacks that might have been registered.
        applyCallbacks(ob, r, REQUEST, RESPONSE)

        # Finish metadata with an empty line.
        r.append('')
        metadata = join(r, '\n')
        metadata_len = len(metadata)

        # Check if we should send the file's data down the response.
        if REQUEST.get('skip_data'):
            # We've been requested to send only the metadata. The
            # client will presumably fetch the data itself.
            self._write_metadata(RESPONSE, metadata, metadata_len)
            return ''

        ob_data = getattr(aq_base(ob), 'data', None)
        if (ob_data is not None and isinstance(ob_data, Image.Pdata)):
            # We have a File instance with chunked data, lets stream it.
            #
            # Note we are setting the content-length header here. This
            # is a simplification. Read comment below.
            #
            # We assume that ob.get_size() will return the exact size
            # of the PData chain. If that assumption is broken we
            # might have problems. This is mainly an optimization. If
            # we read the whole PData chain just to compute the
            # correct size that could cause the whole file to be read
            # into memory.
            RESPONSE.setHeader('Content-Length', ob.get_size())
            # It is safe to use this PDataStreamIterator here because
            # it is consumed right below. This is only used to
            # simplify the code below so it only has to deal with
            # stream iterators or plain strings.
            body = PDataStreamIterator(ob.data)
        elif hasattr(ob, 'manage_FTPget'):
            # Calling manage_FTPget *might* have side-effects. For
            # example, in Archetypes it does set the 'content-type'
            # response header, which would end up overriding our own
            # content-type header because we've set it 'too
            # early'. We've moved setting the content-type header to
            # the '_write_metadata' method since, and any manipulation
            # of response headers should happen there, if possible.
            try:
                body = ob.manage_FTPget()
            except TypeError: # some need the R/R pair!
                body = ob.manage_FTPget(REQUEST, RESPONSE)
        elif hasattr(ob, 'EditableBody'):
            body = ob.EditableBody()
        elif hasattr(ob, 'document_src'):
            body = ob.document_src(REQUEST, RESPONSE)
        elif hasattr(ob, 'read'):
            body = ob.read()
        else:
            # can't read it!
            raise 'BadRequest', 'Object does not support external editing'

        if (HAVE_Z3_IFACE and IStreamIterator.providedBy(body) or
            (not HAVE_Z3_IFACE) and IStreamIterator.isImplementedBy(body)):
            # We need to manage our content-length because we're streaming.
            # The content-length should have been set in the response by
            # the method that returns the iterator, but we need to fix it up
            # here because we insert metadata before the body.
            clen = RESPONSE.headers.get('content-length', None)
            assert clen is not None
            self._write_metadata(RESPONSE, metadata, metadata_len + int(clen))
            for data in body:
                RESPONSE.write(data)
            return ''

        # If we reached this point, body *must* be a string. We *must*
        # set the headers ourselves since _write_metadata won't get
        # called.
        self._set_headers(RESPONSE)
        return join((metadata, body), '\n')

    def _set_headers(self, RESPONSE):
        # Using RESPONSE.setHeader('Pragma', 'no-cache') would be better, but
        # this chokes crappy most MSIE versions when downloads happen on SSL.
        # cf. http://support.microsoft.com/support/kb/articles/q316/4/31.asp
        #RESPONSE.setHeader('Last-Modified', rfc1123_date())
        RESPONSE.setHeader('Content-Type', 'application/x-zope-edit')
        
        # We have to test the msie behaviour
        user_agent = self.REQUEST.get_header('User-Agent')
        if user_agent and (("msie" in user_agent.lower())
            or ("microsoft internet explorer" in user_agent.lower())):
            RESPONSE.setHeader('Cache-Control', 'must-revalidate, post-check=0, pre-check=0')
            RESPONSE.setHeader('Pragma', 'public')
        else:
            RESPONSE.setHeader('Pragma', 'no-cache')
        now = rfc1123_date()
        RESPONSE.setHeader('Last-Modified', now)
        RESPONSE.setHeader('Expires', now)

    def _write_metadata(self, RESPONSE, metadata, length):
        # Set response content-type so that the browser gets hinted
        # about what application should handle this.
        self._set_headers(RESPONSE)

        # Set response length and write our metadata. The '+1' on the
        # content-length is the '\n' after the metadata.
        RESPONSE.setHeader('Content-Length', length + 1)
        RESPONSE.write(metadata)
        RESPONSE.write('\n')

InitializeClass(ExternalEditor)


def EditLink(self, object, borrow_lock=0, skip_data=0):
    """Insert the external editor link to an object if appropriate"""
    base = aq_base(object)
    user = getSecurityManager().getUser()
    editable = (hasattr(base, 'manage_FTPget')
                or hasattr(base, 'EditableBody')
                or hasattr(base, 'document_src')
                or hasattr(base, 'read'))
    if editable and user.has_permission(ExternalEditorPermission, object):
        query = {}
        # Add extension to URL so that the Client
        # launch the ZopeEditManager helper app
        # this is a workaround for limited MIME type
        ext = '.zem'
        if borrow_lock:
            query['borrow_lock'] = 1
        if skip_data:
            query['skip_data'] = 1
        url = "%s/externalEdit_/%s%s%s" % (aq_parent(aq_inner(object)).absolute_url(),
                                           urllib.quote(object.getId()),
                                           ext, querystr(query))
        return ('<a href="%s" '
                'title="Edit using external editor">'
                '<img src="%s/misc_/ExternalEditor/edit_icon" '
                'align="middle" hspace="2" border="0" alt="External Editor" />'
                '</a>' % (url, object.REQUEST.BASEPATH1)
               )
    else:
        return ''

def querystr(d):
    """Create a query string from a dict"""
    if d:
        return '?' + '&'.join(
            ['%s=%s' % (name, val) for name, val in d.items()])
    else:
        return ''

