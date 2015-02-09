import unittest
import zope.component.testing

from zope.component import provideUtility
from zope.component import provideAdapter

from plone.registry.interfaces import IRegistry
from plone.registry import Registry

from plone.registry.fieldfactory import persistentFieldAdapter

from plone.cachepurging.interfaces import ICachePurgingSettings
from plone.cachepurging.rewrite import DefaultRewriter

class FauxRequest(dict):
    pass

class TestRewrite(unittest.TestCase):

    def setUp(self):
        self.request = FauxRequest()
        self.rewriter = DefaultRewriter(self.request)
        provideAdapter(persistentFieldAdapter)

    def tearDown(self):
        zope.component.testing.tearDown()

    def _prepareVHMRequest(self, path, domain='example.com', root='/plone', prefix='', protocol='http'):
        translatedPrefix = '/'.join(['_vh_%s' % p for p in prefix.split('/')])

        self.request['URL'] = '%s://%s%s%s' % (protocol, domain, prefix, path,)
        self.request['ACTUAL_URL'] = '%s://%s%s%s' % (protocol, domain, prefix, path,)
        self.request['SERVER_URL'] = '%s://%s' % (protocol, domain,)
        self.request['PATH_INFO'] = '/VirtualHostBase/%s/%s:80%s/VirtualHostRoot%s%s' % (protocol, domain, root, translatedPrefix, path,)
        self.request['VIRTUAL_URL'] = '%s://%s%s' % (protocol, domain, path)

        if prefix:
            self.request['VIRTUAL_URL_PARTS'] = ('%s://%s' % (protocol, domain,), prefix[1:], path[1:])
        else:
            self.request['VIRTUAL_URL_PARTS'] = ('%s://%s' % (protocol, domain,), path[1:])

        self.request['VirtualRootPhysicalPath'] = tuple(root.split('/'))

    def test_no_registry(self):
        self._prepareVHMRequest('/foo')
        self.assertEqual(['/foo'], self.rewriter('/foo'))

    def test_no_settings(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        self._prepareVHMRequest('/foo')
        self.assertEqual(['/foo'], self.rewriter('/foo'))

    def test_virtual_hosting_disabled(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = False

        self._prepareVHMRequest('/foo')
        self.assertEqual(['/foo'], self.rewriter('/foo'))

    def test_empty_request(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self.request.clear()
        self.assertEqual(['/foo'], self.rewriter('/foo'))

    def test_no_virtual_url(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('/foo')
        del self.request['VIRTUAL_URL']
        self.assertEqual(['/foo'], self.rewriter('/foo'))

    def test_no_virtual_url_parts(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('/foo')
        del self.request['VIRTUAL_URL_PARTS']
        self.assertEqual(['/foo'], self.rewriter('/foo'))

    def test_no_virtual_root_physical_path(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('/foo')
        del self.request['VirtualRootPhysicalPath']
        self.assertEqual(['/foo'], self.rewriter('/foo'))

    def test_malformed_virtual_url_parts(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('/foo')

        self.request['VIRTUAL_URL_PARTS'] = ('foo',)
        self.assertEqual(['/foo'], self.rewriter('/foo'))

        self.request['VIRTUAL_URL_PARTS'] = ()
        self.assertEqual(['/foo'], self.rewriter('/foo'))

        self.request['VIRTUAL_URL_PARTS'] = ('http://example.com', '', '/foo', 'x')
        self.assertEqual(['/foo'], self.rewriter('/foo'))

        self.request['VIRTUAL_URL_PARTS'] = 'foo'
        self.assertEqual(['/foo'], self.rewriter('/foo'))

    def test_standard_vhm(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('/foo')
        self.assertEqual(['/VirtualHostBase/http/example.com/plone/VirtualHostRoot/foo'],
                          self.rewriter('/foo'))

    def test_virtual_root_is_app_root(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('/foo', root='/')

        self.assertEqual(['/VirtualHostBase/http/example.com/VirtualHostRoot/foo'],
                          self.rewriter('/foo'))

    def test_virtual_root_is_deep(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('/foo', root='/bar/plone')

        self.assertEqual(['/VirtualHostBase/http/example.com/bar/plone/VirtualHostRoot/foo'],
                          self.rewriter('/foo'))

    def test_inside_out_hosting(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('/foo', root='/bar/plone', prefix='/foo/bar')

        self.assertEqual(['/VirtualHostBase/http/example.com/bar/plone/VirtualHostRoot/_vh_foo/_vh_bar/foo'],
                          self.rewriter('/foo'))

    def test_virtual_path_is_root(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('/', root='/plone')

        self.assertEqual(['/VirtualHostBase/http/example.com/plone/VirtualHostRoot/'],
                          self.rewriter('/'))

    def test_virtual_path_is_empty(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('', root='/plone')

        self.assertEqual(['/VirtualHostBase/http/example.com/plone/VirtualHostRoot/'],
                          self.rewriter(''))

    def test_virtual_path_is_deep(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('/foo/bar', root='/plone')

        self.assertEqual(['/VirtualHostBase/http/example.com/plone/VirtualHostRoot/foo/bar'],
                          self.rewriter('/foo/bar'))

    def test_nonstandard_port(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('/foo', domain='example.com:81')
        self.assertEqual(['/VirtualHostBase/http/example.com:81/plone/VirtualHostRoot/foo'],
                          self.rewriter('/foo'))

    def test_https(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True

        self._prepareVHMRequest('/foo', domain='example.com:81', protocol='https')
        self.assertEqual(['/VirtualHostBase/https/example.com:81/plone/VirtualHostRoot/foo'],
                          self.rewriter('/foo'))

    def test_domains(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True
        settings.domains = ('http://example.org:81', 'https://example.com:82')

        self._prepareVHMRequest('/foo', domain='example.com:81', protocol='https')
        self.assertEqual(['/VirtualHostBase/http/example.org:81/plone/VirtualHostRoot/foo',
                           '/VirtualHostBase/https/example.com:82/plone/VirtualHostRoot/foo'],
                          self.rewriter('/foo'))

    def test_domains_w_different_path_in_request(self):
        registry = Registry()
        provideUtility(registry, IRegistry)
        registry.registerInterface(ICachePurgingSettings)
        settings = registry.forInterface(ICachePurgingSettings)
        settings.virtualHosting = True
        settings.domains = ('http://example.org:81', 'https://example.com:82')

        self._prepareVHMRequest('/bar', domain='example.com:81', protocol='https')
        self.assertEqual(['/VirtualHostBase/http/example.org:81/plone/VirtualHostRoot/foo',
                           '/VirtualHostBase/https/example.com:82/plone/VirtualHostRoot/foo'],
                          self.rewriter('/foo'))

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
