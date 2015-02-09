##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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
"""Functional tests for virtual hosting.
"""
import os
import unittest
from StringIO import StringIO

import transaction

from zope.browserresource.resource import Resource
from zope.configuration import xmlconfig
from zope.container.contained import Contained
from zope.pagetemplate.pagetemplate import PageTemplate
from zope.pagetemplate.engine import AppPT
from zope.publisher.browser import BrowserRequest
from zope.publisher.publish import publish
from zope.publisher.skinnable import setDefaultSkin
from zope.security.checker import defineChecker, NamesChecker, NoProxy
from zope.security.checker import _checkers, undefineChecker
from zope.site.folder import Folder
from zope.site.folder import rootFolder
from zope.testing.cleanup import cleanUp
from zope.traversing.api import traverse
from zope.traversing.testing import browserResource


class MyObj(Contained):
    def __getitem__(self, key):
        return traverse(self, '/foo/bar/' + key)


class MyPageTemplate(AppPT, PageTemplate):

    def pt_getContext(self, instance, request, **_kw):
        # instance is a View component
        namespace = super(MyPageTemplate, self).pt_getContext(**_kw)
        namespace['template'] = self
        namespace['request'] = request
        namespace['container'] = namespace['context'] = instance
        return namespace

    def render(self, instance, request, *args, **kw):
        return self.pt_render(self.pt_getContext(instance, request))


class MyPageEval(object):

    def index(self, **kw):
        """Call a Page Template"""
        template = self.context
        request = self.request
        return template.render(template.__parent__, request, **kw)


class MyFolderPage(object):

    def index(self, **kw):
        """My folder page"""
        self.request.response.redirect('index.html')
        return ''


class TestVirtualHosting(unittest.TestCase):

    def setUp(self):
        f = os.path.join(os.path.split(__file__)[0], 'ftesting.zcml')
        xmlconfig.file(f)
        self.app = rootFolder()
        defineChecker(MyObj, NoProxy)

    def tearDown(self):
        undefineChecker(MyObj)
        cleanUp()

    def makeRequest(self, path=''):
        env = {"HTTP_HOST": 'localhost',
               "HTTP_REFERER": 'localhost'}
        p = path.split('?')
        if len(p) == 1:
            env['PATH_INFO'] = p[0]

        request = BrowserRequest(StringIO(''), env)
        request.setPublication(DummyPublication(self.app))
        setDefaultSkin(request)
        return request

    def publish(self, path):
        return publish(self.makeRequest(path)).response

    def test_request_url(self):
        self.addPage('/pt', u'<span tal:replace="request/URL"/>')
        self.verify('/pt', 'http://localhost/pt/index.html')
        self.verify('/++vh++/++/pt',
                    'http://localhost/pt/index.html')
        self.verify('/++vh++https:localhost:443/++/pt',
                    'https://localhost/pt/index.html')
        self.verify('/++vh++https:localhost:443/fake/folders/++/pt',
                    'https://localhost/fake/folders/pt/index.html')

        self.addPage('/foo/bar/pt', u'<span tal:replace="request/URL"/>')
        self.verify('/foo/bar/pt', 'http://localhost/foo/bar/pt/index.html')
        self.verify('/foo/bar/++vh++/++/pt',
                    'http://localhost/pt/index.html')
        self.verify('/foo/bar/++vh++https:localhost:443/++/pt',
                    'https://localhost/pt/index.html')
        self.verify('/foo/++vh++https:localhost:443/fake/folders/++/bar/pt',
                    'https://localhost/fake/folders/bar/pt/index.html')

    def test_request_redirect(self):
        self.addPage('/foo/index.html', u'Spam')
        self.verifyRedirect('/foo', 'http://localhost/foo/index.html')
        self.verifyRedirect('/++vh++https:localhost:443/++/foo',
                            'https://localhost/foo/index.html')
        self.verifyRedirect('/foo/++vh++https:localhost:443/bar/++',
                            'https://localhost/bar/index.html')

    def test_absolute_url(self):
        self.addPage('/pt', u'<span tal:replace="context/@@absolute_url"/>')
        self.verify('/pt', 'http://localhost')
        self.verify('/++vh++/++/pt',
                    'http://localhost')
        self.verify('/++vh++https:localhost:443/++/pt',
                    'https://localhost')
        self.verify('/++vh++https:localhost:443/fake/folders/++/pt',
                    'https://localhost/fake/folders')

        self.addPage('/foo/bar/pt',
                     u'<span tal:replace="context/@@absolute_url"/>')
        self.verify('/foo/bar/pt', 'http://localhost/foo/bar')
        self.verify('/foo/bar/++vh++/++/pt',
                    'http://localhost')
        self.verify('/foo/bar/++vh++https:localhost:443/++/pt',
                    'https://localhost')
        self.verify('/foo/++vh++https:localhost:443/fake/folders/++/bar/pt',
                    'https://localhost/fake/folders/bar')

    def test_absolute_url_absolute_traverse(self):
        self.createObject('/foo/bar/obj', MyObj())
        self.addPage('/foo/bar/pt',
                     u'<span tal:replace="container/obj/pt/@@absolute_url"/>')
        self.verify('/foo/bar/pt', 'http://localhost/foo/bar/pt')
        self.verify('/foo/++vh++https:localhost:443/++/bar/pt',
                    'https://localhost/bar/pt')

    def test_resources(self):
        browserResource('quux', Resource)
        # Only register the checker once, so that multiple test runs pass.
        if Resource not in _checkers:
            defineChecker(Resource, NamesChecker(['__call__']))
        self.addPage('/foo/bar/pt',
                     u'<span tal:replace="context/++resource++quux" />')
        self.verify('/foo/bar/pt', 'http://localhost/@@/quux')
        self.verify('/foo/++vh++https:localhost:443/fake/folders/++/bar/pt',
                    'https://localhost/fake/folders/@@/quux')

    def createFolders(self, path):
        """addFolders('/a/b/c/d') would traverse and/or create three nested
        folders (a, b, c) and return a tuple (c, 'd') where c is a Folder
        instance at /a/b/c."""
        folder = self.app  #self.connection.root()['Application']
        if path[0] == '/':
            path = path[1:]
        path = path.split('/')
        for id in path[:-1]:
            try:
                folder = folder[id]
            except KeyError:
                folder[id] = Folder()
                folder = folder[id]
        return folder, path[-1]

    def createObject(self, path, obj):
        folder, id = self.createFolders(path)
        folder[id] = obj
        transaction.commit()

    def addPage(self, path, content):
        page = MyPageTemplate()
        page.pt_edit(content, 'text/html')
        self.createObject(path, page)

    def verify(self, path, content):
        result = self.publish(path)
        self.assertEquals(result.getStatus(), 200)
        self.assertEquals(result.consumeBody(), content)

    def verifyRedirect(self, path, location):
        result = self.publish(path)
        self.assertEquals(result.getStatus(), 302)
        self.assertEquals(result.getHeader('Location'), location)


class DummyPublication:

    def __init__(self, app):
        self.app = app

    def beforeTraversal(self, request):
        """Pre-traversal hook.

        This is called *once* before any traversal has been done.
        """

    def getApplication(self, request):
        """Returns the object where traversal should commence.
        """
        return self.app

    def callTraversalHooks(self, request, ob):
        """Invokes any traversal hooks associated with the object.

        This is called before traversing each object.  The ob argument
        is the object that is about to be traversed.
        """

    def traverseName(self, request, ob, name):
        """Traverses to the next object.

        Name must be an ASCII string or Unicode object."""
        if name == 'index.html':
            from zope.component import queryMultiAdapter
            view = queryMultiAdapter((ob, request), name=name)
            if view is None:
                from zope.publisher.interfaces import NotFound
                raise NotFound(ob, name)
            return view
        else:
            from zope.traversing.publicationtraverse \
                import PublicationTraverserWithoutProxy
            t = PublicationTraverserWithoutProxy()
            return t.traverseName(request, ob, name)

    def afterTraversal(self, request, ob):
        """Post-traversal hook.

        This is called after all traversal.
        """

    def callObject(self, request, ob):
        """Call the object, returning the result.

        For GET/POST this means calling it, but for other methods
        (including those of WebDAV and FTP) this might mean invoking
        a method of an adapter.
        """
        from zope.publisher.publish import mapply
        return mapply(ob, request.getPositionalArguments(), request)

    def afterCall(self, request, ob):
        """Post-callObject hook (if it was successful).
        """

    def handleException(self, ob, request, exc_info, retry_allowed=1):
        """Handle an exception

        Either:
        - sets the body of the response, request.response, or
        - raises a Retry exception, or
        - throws another exception, which is a Bad Thing.
        """
        import traceback
        traceback.print_exception(*exc_info)

    def endRequest(self, request, ob):
        """Do any end-of-request cleanup
        """

    def getDefaultTraversal(self, request, ob):
        if hasattr(ob, 'index'):
            return ob, ()
        else:
            return ob, ('index.html',)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestVirtualHosting))
    return suite


if __name__ == '__main__':
    unittest.main()
