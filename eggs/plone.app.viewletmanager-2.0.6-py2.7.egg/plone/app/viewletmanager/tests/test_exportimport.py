from OFS.Folder import Folder

from persistent.dict import PersistentDict
from zope.component import getUtility
from zope.component import getSiteManager
from zope.site.hooks import setHooks, setSite
from five.localsitemanager import make_objectmanager_site

from Products.GenericSetup.tests.common import BaseRegistryTests
from Products.GenericSetup.tests.common import DummyExportContext
from Products.GenericSetup.tests.common import DummyImportContext

from Products.CMFPlone.exportimport.tests.base import BodyAdapterTestCase
from Products.PloneTestCase.layer import PloneSite
from Testing.ZopeTestCase import installPackage

from plone.app.viewletmanager.interfaces import IViewletSettingsStorage
from plone.app.viewletmanager.storage import ViewletSettingsStorage

# BBB Zope 2.12
try:
    from Zope2.App import zcml
    from OFS import metaconfigure
    zcml, metaconfigure     # make pyflakes happy...
    metaconfigure
except ImportError:
    from Products.Five import zcml
    from Products.Five import fiveconfigure as metaconfigure


COMMON_SETUP_ORDER = {
    'basic': {'top': ('one', )},
    'fancy': {'top': ('two', 'three', 'one')},
    }

COMMON_SETUP_HIDDEN = {
    'light': {'top': ('two', )},
    }

_VIEWLETS_XML = """\
<?xml version="1.0"?>
<object>
 <order manager="top" skinname="fancy">
  <viewlet name="two"/>
  <viewlet name="three"/>
  <viewlet name="one"/>
 </order>
 <order manager="top" skinname="basic">
  <viewlet name="one"/>
 </order>
 <hidden manager="top" skinname="light">
  <viewlet name="two"/>
 </hidden>
</object>
"""

_EMPTY_EXPORT = """\
<?xml version="1.0"?>
<object />
"""

_CHILD_PURGE_IMPORT = """\
<?xml version="1.0"?>
<object>
 <order manager="top" skinname="fancy" purge="True" />
 <hidden manager="top" skinname="light" purge="True" />
</object>
"""


_FRAGMENT1_IMPORT = """\
<?xml version="1.0"?>
<object>
 <order manager="top" skinname="fancy">
  <viewlet name="three" insert-before="two"/>
 </order>
</object>
"""

_FRAGMENT2_IMPORT = """\
<?xml version="1.0"?>
<object>
 <order manager="top" skinname="*">
  <viewlet name="four" insert-after="three"/>
 </order>
</object>
"""

_FRAGMENT3_IMPORT = """\
<?xml version="1.0"?>
<object>
 <order manager="top" skinname="*">
  <viewlet name="three" insert-before="*"/>
  <viewlet name="four" insert-after="*"/>
 </order>
</object>
"""

_FRAGMENT4_IMPORT = """\
<?xml version="1.0"?>
<object>
 <order manager="top" skinname="*">
  <viewlet name="three" remove="1"/>
 </order>
</object>
"""

_FRAGMENT5_IMPORT = """\
<?xml version="1.0"?>
<object>
 <order manager='top' skinname="existing" based-on="fancy">
 </order>
 <order manager='top' skinname="new" based-on="fancy">
  <viewlet name="three" insert-before="two"/>
 </order>
 <order manager='top' skinname="wrongbase" based-on="invalid_base_id">
  <viewlet name="two"/>
 </order>
</object>"""

_FRAGMENT6_IMPORT = """\
<?xml version="1.0"?>
<object>
 <order manager="top" skinname="added" make_default="True">
  <viewlet name="one"/>
  <viewlet name="two"/>
  <viewlet name="three"/>
 </order>
 <hidden manager="top" skinname="added" make_default="True">
  <viewlet name="two"/>
 </hidden>
</object>
"""

_FRAGMENT7_IMPORT = """\
<?xml version="1.0"?>
<object>
  <hidden manager="top" skinname="*" >
    <viewlet name="two"/>
  </hidden>
</object>
"""


class Layer(PloneSite):

    @classmethod
    def setUp(cls):
        from zope.component import provideAdapter
        from plone.app.viewletmanager.exportimport.storage import ViewletSettingsStorageNodeAdapter
        from Products.GenericSetup.interfaces import IBody
        from Products.GenericSetup.interfaces import ISetupEnviron

        metaconfigure.debug_mode = True
        import plone.app.vocabularies
        zcml.load_config('configure.zcml', plone.app.vocabularies)
        metaconfigure.debug_mode = False
        installPackage('plone.app.vocabularies', quiet=True)

        provideAdapter(factory=ViewletSettingsStorageNodeAdapter,
            adapts=(IViewletSettingsStorage, ISetupEnviron),
            provides=IBody)


class ViewletSettingsStorageXMLAdapterTests(BodyAdapterTestCase):

    layer = Layer

    def _getTargetClass(self):
        from plone.app.viewletmanager.exportimport.storage \
                    import ViewletSettingsStorageNodeAdapter
        return ViewletSettingsStorageNodeAdapter

    def _populate(self, obj):
        obj.setOrder('top', 'fancy', ('two', 'three', 'one'))
        obj.setOrder('top', 'basic', ('one', ))
        obj.setHidden('top', 'light', ('two', ))

    def _verifyImport(self, obj):
        fancydict = {'top': ('two', 'three', 'one')}
        hiddendict = {'top': ('two', )}
        self.assertEqual(type(obj._order), PersistentDict)
        self.failUnless('fancy' in obj._order.keys())
        self.assertEqual(type(obj._order['fancy']), PersistentDict)
        self.assertEqual(dict(obj._order['fancy']), fancydict)
        self.assertEqual(type(obj._hidden), PersistentDict)
        self.failUnless('light' in obj._hidden.keys())
        self.assertEqual(type(obj._hidden['light']), PersistentDict)
        self.assertEqual(dict(obj._hidden['light']), hiddendict)

    def setUp(self):
        setHooks()
        self.site = Folder('site')
        make_objectmanager_site(self.site)
        setSite(self.site)
        sm = getSiteManager()
        sm.registerUtility(ViewletSettingsStorage(), IViewletSettingsStorage)

        self._obj = getUtility(IViewletSettingsStorage)

        self._BODY = _VIEWLETS_XML

    def tearDown(self):
        sm = getSiteManager(self.site)
        sm.unregisterUtility(self._obj, IViewletSettingsStorage)


class _ViewletSettingsStorageSetup(BaseRegistryTests):

    layer = Layer

    def setUp(self):
        BaseRegistryTests.setUp(self)
        setHooks()
        self.app.site = Folder(id='site')
        self.site = self.app.site
        make_objectmanager_site(self.site)
        setSite(self.site)
        sm = getSiteManager(self.site)
        sm.registerUtility(ViewletSettingsStorage(), IViewletSettingsStorage)
        self.storage = getUtility(IViewletSettingsStorage)

    def afterSetUp(self):
        # avoid setting up an unrestricted user, which causes test isolation issues
        pass

    def tearDown(self):
        sm = getSiteManager(self.site)
        sm.unregisterUtility(self.storage, IViewletSettingsStorage)

    def _populateSite(self, order={}, hidden={}):
        storage = self.storage
        for skinname in order.keys():
            for manager in order[skinname].keys():
                self.storage.setOrder(manager, skinname,
                                            order[skinname][manager])

        for skinname in hidden.keys():
            for manager in hidden[skinname].keys():
                self.storage.setHidden(manager, skinname,
                                            hidden[skinname][manager])


class exportViewletSettingsStorageTests(_ViewletSettingsStorageSetup):

    def test_empty(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                exportViewletSettingsStorage

        context = DummyExportContext(self.site)
        exportViewletSettingsStorage(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'viewlets.xml')
        self._compareDOM(text, _EMPTY_EXPORT)
        self.assertEqual(content_type, 'text/xml')

    def test_normal(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                exportViewletSettingsStorage

        _ORDER = COMMON_SETUP_ORDER
        _HIDDEN = COMMON_SETUP_HIDDEN
        self._populateSite(order=_ORDER, hidden=_HIDDEN)

        context = DummyExportContext(self.site)
        exportViewletSettingsStorage(context)

        self.assertEqual(len(context._wrote), 1)
        filename, text, content_type = context._wrote[0]
        self.assertEqual(filename, 'viewlets.xml')
        self._compareDOM(text, _VIEWLETS_XML)
        self.assertEqual(content_type, 'text/xml')


class importViewletSettingsStorageTests(_ViewletSettingsStorageSetup):

    _VIEWLETS_XML = _VIEWLETS_XML
    _EMPTY_EXPORT = _EMPTY_EXPORT
    _CHILD_PURGE_IMPORT = _CHILD_PURGE_IMPORT
    _FRAGMENT1_IMPORT = _FRAGMENT1_IMPORT
    _FRAGMENT2_IMPORT = _FRAGMENT2_IMPORT
    _FRAGMENT3_IMPORT = _FRAGMENT3_IMPORT
    _FRAGMENT4_IMPORT = _FRAGMENT4_IMPORT
    _FRAGMENT5_IMPORT = _FRAGMENT5_IMPORT
    _FRAGMENT6_IMPORT = _FRAGMENT6_IMPORT
    _FRAGMENT7_IMPORT = _FRAGMENT7_IMPORT

    def test_empty_default_purge(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                importViewletSettingsStorage

        _ORDER = COMMON_SETUP_ORDER
        _HIDDEN = COMMON_SETUP_HIDDEN
        self._populateSite(order=_ORDER, hidden=_HIDDEN)


        site = self.site
        utility = self.storage

        self.assertEqual(len(utility.getOrder('top', 'fancy')), 3)
        self.assertEqual(len(utility.getOrder('top', 'basic')), 1)
        self.assertEqual(len(utility.getHidden('top', 'light')), 1)
        self.assertEqual(len(utility.getOrder('top', 'undefined')), 3)

        context = DummyImportContext(site)
        context._files['viewlets.xml'] = self._EMPTY_EXPORT
        importViewletSettingsStorage(context)

        self.assertEqual(len(utility.getOrder('top', 'fancy')), 0)
        self.assertEqual(len(utility.getOrder('top', 'basic')), 0)
        self.assertEqual(len(utility.getHidden('top', 'light')), 0)
        self.assertEqual(len(utility.getOrder('top', 'undefined')), 0)

    def test_empty_explicit_purge(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                importViewletSettingsStorage

        _ORDER = COMMON_SETUP_ORDER
        _HIDDEN = COMMON_SETUP_HIDDEN
        self._populateSite(order=_ORDER, hidden=_HIDDEN)

        site = self.site
        utility = self.storage

        self.assertEqual(len(utility.getOrder('top', 'fancy')), 3)
        self.assertEqual(len(utility.getOrder('top', 'basic')), 1)
        self.assertEqual(len(utility.getHidden('top', 'light')), 1)
        self.assertEqual(len(utility.getOrder('top', 'undefined')), 3)

        context = DummyImportContext(site, True)
        context._files['viewlets.xml'] = self._EMPTY_EXPORT
        importViewletSettingsStorage(context)

        self.assertEqual(len(utility.getOrder('top', 'fancy')), 0)
        self.assertEqual(len(utility.getOrder('top', 'basic')), 0)
        self.assertEqual(len(utility.getHidden('top', 'light')), 0)
        self.assertEqual(len(utility.getOrder('top', 'undefined')), 0)

    def test_empty_skip_purge(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                importViewletSettingsStorage

        _ORDER = COMMON_SETUP_ORDER
        _HIDDEN = COMMON_SETUP_HIDDEN
        self._populateSite(order=_ORDER, hidden=_HIDDEN)

        site = self.site
        utility = self.storage

        self.assertEqual(len(utility.getOrder('top', 'fancy')), 3)
        self.assertEqual(len(utility.getOrder('top', 'basic')), 1)
        self.assertEqual(len(utility.getHidden('top', 'light')), 1)
        self.assertEqual(len(utility.getOrder('top', 'undefined')), 3)

        context = DummyImportContext(site, False)
        context._files['viewlets.xml'] = self._EMPTY_EXPORT
        importViewletSettingsStorage(context)

        self.assertEqual(len(utility.getOrder('top', 'fancy')), 3)
        self.assertEqual(len(utility.getOrder('top', 'basic')), 1)
        self.assertEqual(len(utility.getHidden('top', 'light')), 1)
        self.assertEqual(len(utility.getOrder('top', 'undefined')), 3)

    def test_specific_child_purge(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                importViewletSettingsStorage

        _ORDER = COMMON_SETUP_ORDER
        _HIDDEN = COMMON_SETUP_HIDDEN
        self._populateSite(order=_ORDER, hidden=_HIDDEN)

        site = self.site
        utility = self.storage

        self.assertEqual(len(utility.getOrder('top', 'fancy')), 3)
        self.assertEqual(len(utility.getOrder('top', 'basic')), 1)
        self.assertEqual(len(utility.getHidden('top', 'light')), 1)
        self.assertEqual(len(utility.getOrder('top', 'undefined')), 3)

        context = DummyImportContext(site, False)
        context._files['viewlets.xml'] = self._CHILD_PURGE_IMPORT
        importViewletSettingsStorage(context)

        self.assertEqual(len(utility.getOrder('top', 'fancy')), 0)
        self.assertEqual(len(utility.getOrder('top', 'basic')), 1)
        self.assertEqual(len(utility.getHidden('top', 'light')), 0)
        self.assertEqual(len(utility.getOrder('top', 'undefined')), 0)

    def test_normal(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                importViewletSettingsStorage

        site = self.site
        utility = self.storage
        self.assertEqual(len(utility._order.keys()), 0)
        self.assertEqual(len(utility._hidden.keys()), 0)

        context = DummyImportContext(site, False)
        context._files['viewlets.xml'] = self._VIEWLETS_XML
        importViewletSettingsStorage(context)

        self.assertEqual(utility.getOrder('top', 'fancy'),
                                            ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'undefined (fallback)'),
                                            ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'basic'), ('one', ))
        self.assertEqual(utility.getHidden('top', 'light'), ('two', ))

    def test_fragment_skip_purge(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                importViewletSettingsStorage

        _ORDER = COMMON_SETUP_ORDER
        _HIDDEN = COMMON_SETUP_HIDDEN
        self._populateSite(order=_ORDER, hidden=_HIDDEN)

        site = self.site
        utility = self.storage
        self.assertEqual(len(utility._order.keys()), 2)
        self.assertEqual(len(utility._hidden.keys()), 1)

        self.assertEqual(utility.getOrder('top', 'fancy'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'undefined (fallback)'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'basic'), ('one', ))
        self.assertEqual(utility.getHidden('top', 'light'), ('two', ))

        context = DummyImportContext(site, False)
        context._files['viewlets.xml'] = self._FRAGMENT1_IMPORT
        importViewletSettingsStorage(context)

        self.assertEqual(utility.getOrder('top', 'basic'), ('one', ))
        self.assertEqual(utility.getOrder('top', 'fancy'),
                                            ('three', 'two', 'one'))
        self.assertEqual(utility.getHidden('top', 'light'), ('two', ))

        context._files['viewlets.xml'] = self._FRAGMENT2_IMPORT
        importViewletSettingsStorage(context)

        #self.assertEqual(len(utility._order.keys()), 2)
        self.assertEqual(len(utility._order.keys()), 3)

        self.assertEqual(len(utility._hidden.keys()), 1)

        self.assertEqual(utility.getOrder('top', 'fancy'),
                                    ('three', 'four', 'two', 'one'))
        self.assertEqual(utility.getOrder('top', 'basic'),
                                            ('one', 'four'))
        self.assertEqual(utility.getOrder('top', 'light'),
                                            ('four', ))
        self.assertEqual(utility.getHidden('top', 'light'), ('two', ))

        context._files['viewlets.xml'] = self._FRAGMENT1_IMPORT
        importViewletSettingsStorage(context)

        self.assertEqual(utility.getOrder('top', 'fancy'),
                                    ('four', 'three', 'two', 'one'))

    def test_fragment3_skip_purge(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                importViewletSettingsStorage

        _ORDER = COMMON_SETUP_ORDER
        _HIDDEN = COMMON_SETUP_HIDDEN
        self._populateSite(order=_ORDER, hidden=_HIDDEN)

        site = self.site
        utility = self.storage
        self.assertEqual(len(utility._order.keys()), 2)
        self.assertEqual(len(utility._hidden.keys()), 1)

        self.assertEqual(utility.getOrder('top', 'fancy'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'undefined (fallback)'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'basic'), ('one', ))
        self.assertEqual(utility.getHidden('top', 'light'), ('two', ))

        context = DummyImportContext(site, False)
        context._files['viewlets.xml'] = self._FRAGMENT3_IMPORT
        importViewletSettingsStorage(context)
        self.assertEqual(utility.getOrder('top', 'basic'),
                                                ('three', 'one', 'four'))
        self.assertEqual(utility.getOrder('top', 'fancy'),
                                            ('three', 'two', 'one', 'four'))
        self.assertEqual(utility.getOrder('top', 'light'),
                                            ('three', 'four'))
        self.assertEqual(utility.getHidden('top', 'light'), ('two', ))

    def test_fragment4_remove(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                importViewletSettingsStorage

        _ORDER = COMMON_SETUP_ORDER
        _HIDDEN = COMMON_SETUP_HIDDEN
        self._populateSite(order=_ORDER, hidden=_HIDDEN)

        site = self.site
        utility = self.storage
        self.assertEqual(len(utility._order.keys()), 2)
        self.assertEqual(len(utility._hidden.keys()), 1)

        self.assertEqual(utility.getOrder('top', 'fancy'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'undefined (fallback)'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'basic'), ('one', ))
        self.assertEqual(utility.getHidden('top', 'light'), ('two', ))

        context = DummyImportContext(site, False)
        context._files['viewlets.xml'] = self._FRAGMENT4_IMPORT
        importViewletSettingsStorage(context)

        self.assertEqual(utility.getOrder('top', 'basic'), ('one', ))
        self.assertEqual(utility.getOrder('top', 'fancy'), ('two', 'one'))
        self.assertEqual(utility.getHidden('top', 'light'), ('two', ))

    def test_fragment5_based_on(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                importViewletSettingsStorage

        _ORDER = COMMON_SETUP_ORDER
        _HIDDEN = COMMON_SETUP_HIDDEN
        self._populateSite(order=_ORDER, hidden=_HIDDEN)

        site = self.site
        utility = self.storage
        self.assertEqual(len(utility._order.keys()), 2)
        self.assertEqual(len(utility._hidden.keys()), 1)

        self.assertEqual(utility.getOrder('top', 'fancy'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'undefined (fallback)'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'basic'), ('one', ))
        self.assertEqual(utility.getHidden('top', 'light'), ('two', ))

        context = DummyImportContext(site, False)
        context._files['viewlets.xml'] = self._FRAGMENT5_IMPORT
        importViewletSettingsStorage(context)

        self.assertEqual(len(utility._order.keys()), 5)

        self.assertEqual(utility.getOrder('top', 'fancy'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'existing'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'new'),
                                    ('three', 'two', 'one'))
        self.assertEqual(utility.getOrder('top', 'wrongbase'), ('two', ))
        self.assertEqual(utility.getOrder('top', 'undefined (fallback)'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'basic'), ('one', ))
        self.assertEqual(utility.getHidden('top', 'light'), ('two', ))

    def test_fragment6_make_default(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                importViewletSettingsStorage

        _ORDER = COMMON_SETUP_ORDER
        _HIDDEN = COMMON_SETUP_HIDDEN
        self._populateSite(order=_ORDER, hidden=_HIDDEN)

        site = self.site
        utility = self.storage
        self.assertEqual(len(utility._order.keys()), 2)
        self.assertEqual(len(utility._hidden.keys()), 1)

        self.assertEqual(utility.getOrder('top', 'fancy'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'undefined (fallback)'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'basic'), ('one', ))
        self.assertEqual(utility.getHidden('top', 'light'), ('two', ))

        context = DummyImportContext(site, False)
        context._files['viewlets.xml'] = self._FRAGMENT6_IMPORT
        importViewletSettingsStorage(context)

        self.assertEqual(utility.getOrder('top', 'undefined'),
                                        ('one', 'two', 'three'))
        self.assertEqual(utility.getHidden('top', 'undefined'), ('two', ))

    def test_fragment7_make_default(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                importViewletSettingsStorage

        _ORDER = COMMON_SETUP_ORDER
        _HIDDEN = COMMON_SETUP_HIDDEN

        self._populateSite(order=_ORDER, hidden=_HIDDEN)

        site = self.site
        utility = self.storage
        self.assertEqual(len(utility._order.keys()), 2)
        self.assertEqual(len(utility._hidden.keys()), 1)

        self.assertEqual(utility.getOrder('top', 'fancy'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'undefined (fallback)'),
                                    ('two', 'three', 'one'))
        self.assertEqual(utility.getOrder('top', 'basic'), ('one', ))
        self.assertEqual(utility.getHidden('top', 'light'), ('two', ))

        context = DummyImportContext(site, False)
        context._files['viewlets.xml'] = self._FRAGMENT7_IMPORT
        importViewletSettingsStorage(context)
        self.assertEqual(utility.getHidden('top', 'fancy'), ('two', ))
        self.assertEqual(utility.getHidden('top', 'basic'), ('two', ))

    def test_syntax_error_reporting(self):
        from plone.app.viewletmanager.exportimport.storage import \
                                                importViewletSettingsStorage
        from xml.parsers.expat import ExpatError
        site = self.site
        context = DummyImportContext(site, False)
        context._files['viewlets.xml'] = """<?xml version="1.0"?>\n<"""
        self.assertRaises(ExpatError, importViewletSettingsStorage, context)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(ViewletSettingsStorageXMLAdapterTests))
    suite.addTest(makeSuite(exportViewletSettingsStorageTests))
    suite.addTest(makeSuite(importViewletSettingsStorageTests))
    return suite
