import unittest2 as unittest
from plone.testing.zca import UNIT_TESTING

import os
import tempfile

# Load patch for Zope 2.10
try:
    from ZPublisher import interfaces
except ImportError:
    import ZPublisherEventsBackport


from zope.interface import Interface, implements, alsoProvides
from zope.component import adapts, provideAdapter, provideUtility

from plone.transformchain.interfaces import ITransform, ITransformer
from plone.transformchain.transformer import Transformer
from plone.transformchain.zpublisher import applyTransformOnSuccess

from ZPublisher.HTTPResponse import default_encoding
from ZPublisher.Iterators import filestream_iterator
from ZServer.FTPRequest import FTPRequest


class FauxPubEvent(object):

    def __init__(self, request):
        self.request = request

class IRequestMarker(Interface):
    pass

class IPublishedMarker(Interface):
    pass

class FauxResponse(object):

    def __init__(self, body=''):
        self._body = body
        self.headers = {}

    def getBody(self):
        return self._body
    def setBody(self, body):
        self._body = body

class FauxRequest(dict):

    def __init__(self, published, response=None):
        if response is None:
            response = FauxResponse('<html/>')

        self['PUBLISHED'] = published
        self.response = response
        self.environ = {}

class FauxFTPRequest(FauxRequest, FTPRequest):
    pass

class FauxPublished(object):
    pass

class TestTransformChain(unittest.TestCase):

    layer = UNIT_TESTING

    def setUp(self):
        self.t = Transformer()

    def test_simple(self):

        class Transform1(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 0

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " transformed"

            def transformUnicode(self, result, encoding):
                return result + u" transformed"

            def transformIterable(self, result, encoding):
                return ''.join(result) + ' transformed'

        provideAdapter(Transform1, name=u"test.one")

        published = FauxPublished()
        request = FauxRequest(published)
        result = ["Blah"]
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals("Blah transformed", new_result)

    def test_off_switch(self):

        class Transform1(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 0

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " transformed"

            def transformUnicode(self, result, encoding):
                return result + u" transformed"

            def transformIterable(self, result, encoding):
                return ''.join(result) + ' transformed'

        provideAdapter(Transform1, name=u"test.one")

        published = FauxPublished()
        request = FauxRequest(published)
        request.environ['plone.transformchain.disable'] = True

        result = ["Blah"]
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals(None, new_result)

    def test_ftp_request_not_transformed(self):
        request = FauxFTPRequest(FauxPublished())
        result = ["Blah"]
        new_result = self.t(request, result, 'utf8')
        self.assertEquals(None, new_result)

    def test_transform_string(self):

        class Transform1(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 0

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " One"

            def transformUnicode(self, result, encoding):
                return None

            def transformIterable(self, result, encoding):
                return None

        provideAdapter(Transform1, name=u"test.one")

        published = FauxPublished()
        request = FauxRequest(published)
        result = "Blah"
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals("Blah One", new_result)

    def test_transform_unicode(self):
        class Transform1(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 0

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return None

            def transformUnicode(self, result, encoding):
                return result + u" One"

            def transformIterable(self, result, encoding):
                return None

        provideAdapter(Transform1, name=u"test.one")

        published = FauxPublished()
        request = FauxRequest(published)
        result = u"Blah"
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals(u"Blah One", new_result)

    def test_transform_iterable(self):
        class Transform1(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 0

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return None

            def transformUnicode(self, result, encoding):
                return None

            def transformIterable(self, result, encoding):
                return result + [" One"]

        provideAdapter(Transform1, name=u"test.one")

        published = FauxPublished()
        request = FauxRequest(published)
        result = ["Blah"]
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals(["Blah", " One"], new_result)

    def test_transform_mixed(self):

        class Transform1(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 0

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return None

            def transformUnicode(self, result, encoding):
                return None

            def transformIterable(self, result, encoding):
                return u''.join(result) + u" One"

        class Transform2(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 1

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return None

            def transformUnicode(self, result, encoding):
                return result.encode(encoding) + ' Two'

            def transformIterable(self, result, encoding):
                return None

        class Transform3(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 2

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result.decode(encoding) + u" Three"

            def transformUnicode(self, result, encoding):
                None

            def transformIterable(self, result, encoding):
                return None

        provideAdapter(Transform1, name=u"test.one")
        provideAdapter(Transform2, name=u"test.two")
        provideAdapter(Transform3, name=u"test.three")

        published = FauxPublished()
        request = FauxRequest(published)
        result = ["Blah"]
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals(u"Blah One Two Three", new_result)

    def test_abort(self):

        class Transform1(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 0

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return None

            def transformUnicode(self, result, encoding):
                return None

            def transformIterable(self, result, encoding):
                return None

        provideAdapter(Transform1, name=u"test.one")

        published = FauxPublished()
        request = FauxRequest(published)
        result = ["Blah"]
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals(["Blah"], new_result)

    def test_abort_chain(self):

        class Transform1(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 0

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return "One"

            def transformUnicode(self, result, encoding):
                return "One"

            def transformIterable(self, result, encoding):
                return "One"

        class Transform2(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 1

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return None

            def transformUnicode(self, result, encoding):
                return None

            def transformIterable(self, result, encoding):
                return None

        class Transform3(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 2

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " three"

            def transformUnicode(self, result, encoding):
                return result + u" three"

            def transformIterable(self, result, encoding):
                return ''.join(result) + " three"

        provideAdapter(Transform1, name=u"test.one")
        provideAdapter(Transform2, name=u"test.two")
        provideAdapter(Transform3, name=u"test.three")

        published = FauxPublished()
        request = FauxRequest(published)
        result = ["Blah"]
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals("One three", new_result)

    def test_ordering(self):

        class Transform1(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 100

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " One"

            def transformUnicode(self, result, encoding):
                return result + u" One"

            def transformIterable(self, result, encoding):
                return ''.join(result) + " One"

        class Transform2(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = -100

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " Two"

            def transformUnicode(self, result, encoding):
                return result + u" Two"

            def transformIterable(self, result, encoding):
                return ''.join(result) + " Two"

        class Transform3(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 101

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " Three"

            def transformUnicode(self, result, encoding):
                return result + u" Three"

            def transformIterable(self, result, encoding):
                return ''.join(result) + " Three"

        provideAdapter(Transform1, name=u"test.one")
        provideAdapter(Transform2, name=u"test.two")
        provideAdapter(Transform3, name=u"test.three")

        published = FauxPublished()
        request = FauxRequest(published)
        result = ["Initial"]
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals("Initial Two One Three", new_result)

    def test_request_marker(self):

        class Transform1(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 100

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " One"

            def transformUnicode(self, result, encoding):
                return result + u" One"

            def transformIterable(self, result, encoding):
                return ''.join(result) + " One"

        class Transform2(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = -100

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " Two"

            def transformUnicode(self, result, encoding):
                return result + u" Two"

            def transformIterable(self, result, encoding):
                return ''.join(result) + " Two"

        class Transform3(object):
            implements(ITransform)
            adapts(Interface, IRequestMarker)

            order = 101

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " Three"

            def transformUnicode(self, result, encoding):
                return result + u" Three"

            def transformIterable(self, result, encoding):
                return ''.join(result) + " Three"

        provideAdapter(Transform1, name=u"test.one")
        provideAdapter(Transform2, name=u"test.two")
        provideAdapter(Transform3, name=u"test.three")

        published = FauxPublished()
        request = FauxRequest(published)
        result = ["Initial"]
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals("Initial Two One", new_result)

        published = FauxPublished()
        request = FauxRequest(published)
        alsoProvides(request, IRequestMarker)
        result = ["Initial"]
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals("Initial Two One Three", new_result)

    def test_published_marker(self):

        class Transform1(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = 100

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " One"

            def transformUnicode(self, result, encoding):
                return result + u" One"

            def transformIterable(self, result, encoding):
                return ''.join(result) + " One"

        class Transform2(object):
            implements(ITransform)
            adapts(Interface, Interface)

            order = -100

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " Two"

            def transformUnicode(self, result, encoding):
                return result + u" Two"

            def transformIterable(self, result, encoding):
                return ''.join(result) + " Two"

        class Transform3(object):
            implements(ITransform)
            adapts(IPublishedMarker, Interface)

            order = 101

            def __init__(self, published, request):
                self.published = published
                self.request = request

            def transformBytes(self, result, encoding):
                return result + " Three"

            def transformUnicode(self, result, encoding):
                return result + u" Three"

            def transformIterable(self, result, encoding):
                return ''.join(result) + " Three"

        provideAdapter(Transform1, name=u"test.one")
        provideAdapter(Transform2, name=u"test.two")
        provideAdapter(Transform3, name=u"test.three")

        published = FauxPublished()
        request = FauxRequest(published)
        result = ["Initial"]
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals("Initial Two One", new_result)

        published = FauxPublished()
        alsoProvides(published, IPublishedMarker)
        request = FauxRequest(published)
        result = ["Initial"]
        encoding = 'utf-8'

        new_result = self.t(request, result, encoding)
        self.assertEquals("Initial Two One Three", new_result)

class TestZPublisherTransforms(unittest.TestCase):

    UNIT_TESTING

    def setUp(self):
        self.t = Transformer()

    def test_applyTransform_webdav_port(self):
        class DoNotCallTransformer(object):
            implements(ITransformer)
            encoding = None
            def __call__(self, request, result, encoding):
                raise AssertionError("Shouldn't have been called")

        transformer = DoNotCallTransformer()
        provideUtility(transformer)

        published = FauxPublished()
        request = FauxRequest(published)
        request['WEBDAV_SOURCE_PORT'] = '8081'
        applyTransformOnSuccess(FauxPubEvent(request))

    def test_applyTransform_webdav_method(self):
        class DoNotCallTransformer(object):
            implements(ITransformer)
            encoding = None
            def __call__(self, request, result, encoding):
                raise AssertionError("Shouldn't have been called")

        transformer = DoNotCallTransformer()
        provideUtility(transformer)

        published = FauxPublished()
        request = FauxRequest(published)
        request['REQUEST_METHOD'] = 'PUT'
        applyTransformOnSuccess(FauxPubEvent(request))

    def test_applyTransform_webdav_pathinfo(self):
        class DoNotCallTransformer(object):
            implements(ITransformer)
            encoding = None
            def __call__(self, request, result, encoding):
                raise AssertionError("Shouldn't have been called")

        transformer = DoNotCallTransformer()
        provideUtility(transformer)

        published = FauxPublished()
        request = FauxRequest(published)
        request['PATH_INFO'] = '/foo/bar/manage_DAVget'
        applyTransformOnSuccess(FauxPubEvent(request))

    def test_applyTransform_no_utility(self):
        published = FauxPublished()
        request = FauxRequest(published)
        applyTransformOnSuccess(FauxPubEvent(request))

    def test_applyTransform_default_encoding(self):
        class EncodingCaptureTransformer(object):
            implements(ITransformer)
            encoding = None
            def __call__(self, request, result, encoding):
                self.encoding = encoding

        transformer = EncodingCaptureTransformer()
        provideUtility(transformer)

        published = FauxPublished()
        request = FauxRequest(published)
        applyTransformOnSuccess(FauxPubEvent(request))

        self.assertEquals(default_encoding, transformer.encoding)

    def test_applyTransform_other_encoding(self):
        class EncodingCaptureTransformer(object):
            implements(ITransformer)
            encoding = None
            def __call__(self, request, result, encoding):
                self.encoding = encoding

        transformer = EncodingCaptureTransformer()
        provideUtility(transformer)

        published = FauxPublished()
        request = FauxRequest(published)
        request.response.headers['content-type'] = 'text/html; charset=dummy'
        applyTransformOnSuccess(FauxPubEvent(request))

        self.assertEquals("dummy", transformer.encoding)

    def test_applyTransform_other_encoding_with_header_missing_space(self):
        class EncodingCaptureTransformer(object):
            implements(ITransformer)
            encoding = None
            def __call__(self, request, result, encoding):
                self.encoding = encoding

        transformer = EncodingCaptureTransformer()
        provideUtility(transformer)

        published = FauxPublished()
        request = FauxRequest(published)
        request.response.headers['content-type'] = 'text/html;charset=dummy'
        applyTransformOnSuccess(FauxPubEvent(request))

        self.assertEquals("dummy", transformer.encoding)

    def test_applyTransform_str(self):
        class FauxTransformer(object):
            implements(ITransformer)
            def __call__(self, request, result, encoding):
                return 'dummystr'

        transformer = FauxTransformer()
        provideUtility(transformer)

        published = FauxPublished()
        request = FauxRequest(published)
        applyTransformOnSuccess(FauxPubEvent(request))

        self.assertEquals('dummystr', request.response.getBody())

    def test_applyTransform_unicode(self):
        class FauxTransformer(object):
            implements(ITransformer)
            def __call__(self, request, result, encoding):
                return u'dummystr'

        transformer = FauxTransformer()
        provideUtility(transformer)

        published = FauxPublished()
        request = FauxRequest(published)
        applyTransformOnSuccess(FauxPubEvent(request))

        # note: the real setBody would encode here
        self.assertEquals(u'dummystr', request.response.getBody())

    def test_applyTransform_iterable(self):
        class FauxTransformer(object):
            implements(ITransformer)
            def __call__(self, request, result, encoding):
                return ['iter', 'one']

        transformer = FauxTransformer()
        provideUtility(transformer)

        published = FauxPublished()
        request = FauxRequest(published)
        applyTransformOnSuccess(FauxPubEvent(request))

        self.assertEquals('iterone', request.response.getBody())

    def test_applyTransform_streamiterator(self):
        tmp = tempfile.mkstemp()[1]
        try:

            out = open(tmp, 'w')
            print >> out, "foo"
            out.close()

            class FauxTransformer(object):
                implements(ITransformer)
                def __call__(self, request, result, encoding):
                    return filestream_iterator(tmp)

            transformer = FauxTransformer()
            provideUtility(transformer)

            published = FauxPublished()
            request = FauxRequest(published)
            applyTransformOnSuccess(FauxPubEvent(request))

            self.failUnless(isinstance(request.response.getBody(), filestream_iterator,))
        finally:
            os.unlink(tmp)

    def test_applyTransform_str_input_body(self):
        class FauxTransformer(object):
            implements(ITransformer)
            def __call__(self, request, result, encoding):
                assert isinstance(result, list)
                assert isinstance(result[0], str)
                return 'dummystr'

        transformer = FauxTransformer()
        provideUtility(transformer)

        published = FauxPublished()
        request = FauxRequest(published)
        request.response.setBody("<html />")

        applyTransformOnSuccess(FauxPubEvent(request))

        # note: the real setBody would encode here
        self.assertEquals('dummystr', request.response.getBody())

    def test_applyTransform_unicode_input_body(self):
        class FauxTransformer(object):
            implements(ITransformer)
            def __call__(self, request, result, encoding):
                assert isinstance(result, list)
                assert isinstance(result[0], str)
                return u'dummystr'

        transformer = FauxTransformer()
        provideUtility(transformer)

        published = FauxPublished()
        request = FauxRequest(published)
        request.response.setBody(u"<html />")

        applyTransformOnSuccess(FauxPubEvent(request))

        # note: the real setBody would encode here
        self.assertEquals(u'dummystr', request.response.getBody())
