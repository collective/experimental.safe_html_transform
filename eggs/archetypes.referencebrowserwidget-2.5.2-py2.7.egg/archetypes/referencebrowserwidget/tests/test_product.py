import unittest
import os.path
import re
from urllib import urlencode

import zope.component
import zope.interface
from zope.formlib.namedtemplate import INamedTemplate
from zope.publisher.browser import TestRequest

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five import BrowserView
try:
    from Testing.testbrowser import Browser  # Zope >= 2.13
    Browser   # pyflakes
except ImportError:
    from Products.Five.testbrowser import Browser  # Zope < 2.13

from plone.app.form._named import named_template_adapter
from plone.app.layout.navigation.interfaces import INavigationRoot

from Products.Archetypes.tests.utils import makeContent
from Products.CMFCore.utils import getToolByName
from Products.PloneTestCase.PloneTestCase import default_password
from Products.PloneTestCase.PloneTestCase import portal_owner
try:
    import plone.uuid
    plone.uuid   # pyflakes
    import pkg_resources
    uuid_version = pkg_resources.get_distribution("plone.uuid").version
    if uuid_version < '1.0.2':
        HAS_DASH_UUID = True
    else:
        HAS_DASH_UUID = False
except ImportError:
    HAS_DASH_UUID = False

from Products.CMFPlone import Batch

from archetypes.referencebrowserwidget.tests.base import TestCase
from archetypes.referencebrowserwidget.tests.base import FunctionalTestCase
from archetypes.referencebrowserwidget.tests.base import PopupBaseTestCase
from archetypes.referencebrowserwidget.tests.base import normalize
from archetypes.referencebrowserwidget.tests.base import DummyObject
from archetypes.referencebrowserwidget.interfaces import (
    IFieldRelation, IReferenceBrowserHelperView)
from archetypes.referencebrowserwidget.browser.view import \
    ReferenceBrowserHelperView

_marker = []


class ProductsTestCase(TestCase):
    """ Basic product unit tests """

    def afterSetUp(self):
        self.createDefaultStructure()

    def test_skininstall(self):
        assert 'referencebrowser' in self.portal.portal_skins.objectIds()

    def test_atadapter(self):
        makeContent(self.folder, portal_type='Document', id='doc1')
        makeContent(self.folder, portal_type='Document', id='doc2')
        self.folder.doc1.setRelatedItems(self.folder.doc2)

        field = self.folder.doc1.getField('relatedItems')
        relation = zope.component.getMultiAdapter((self.folder.doc1, field),
                                                  interface=IFieldRelation)
        assert len(relation) == 1
        assert relation[0] == self.folder.doc2

    def test_plonerelationsadapter(self):
        pass
        # XXX test plone.relations implementation

    def test_requiredbehavior_multi(self):
        """ A required field should throw an error, if no value is provided,
            not silently ignore it.
        """
        makeContent(self.folder, portal_type='RefBrowserDemo', id='ref')
        makeContent(self.folder, portal_type='Document', id='doc')

        context = self.folder.ref

        field = context.getField('multiRef')
        field.required = True

        self.folder.doc.reindexObject()
        uid = self.folder.doc.UID()

        # with value
        form = {'singleRef': '',
                'multiRef2': [''],
                'multiRef': [uid]}
        assert field.widget.process_form(context, field, form,
                                         empty_marker=_marker)[0][0] == uid

        # without the key, we have to return the empty marker and do nothing
        form = {'singleRef': '',
                'multiRef2': ['']}
        value = field.widget.process_form(context, field, form,
                                          empty_marker=_marker)
        assert value is _marker

        # without value
        form = {'singleRef': '',
                'multiRef2': [''],
                'multiRef': []}
        value = field.widget.process_form(context, field, form,
                                          empty_marker=_marker)
        assert len(value) == 2
        assert value[0] == []
        assert value[0] is not _marker

        # no value returns empty_marker
        form = {'singleRef': '',
                'multiRef2': ['']}
        value = field.widget.process_form(context, field, form,
                                          emptyReturnsMarker=True,
                                          empty_marker=_marker)
        assert value is _marker

    def test_requiredbehavior_single(self):
        """ A required field should throw an error, if no value is provided,
            not silently ignore it.
        """
        makeContent(self.folder, portal_type='RefBrowserDemo', id='ref')
        makeContent(self.folder, portal_type='Document', id='doc')

        context = self.folder.ref

        field = context.getField('singleRef')
        field.required = True

        self.folder.doc.reindexObject()
        uid = self.folder.doc.UID()

        # with value
        form = {'singleRef': uid,
                'multiRef2': [''],
                'multiRef': []}
        assert field.widget.process_form(context, field, form,
                                         empty_marker=_marker)[0] == uid

        # without key
        form = {'multiRef2': ['']}
        value = field.widget.process_form(context, field, form,
                                          empty_marker=_marker)
        assert value is _marker

        # without value
        form = {'singleRef': '',
                'multiRef2': [''],
                'multiRef': []}
        value = field.widget.process_form(context, field, form,
                                          empty_marker=_marker)
        assert len(value) == 2
        assert value[0] == ''

        # no value returns empty_marker
        form = {}
        value = field.widget.process_form(context, field, form,
                                          emptyReturnsMarker=True,
                                          empty_marker=_marker)
        assert value is _marker


def getPTName(filename):
    basepath, ext = os.path.splitext(filename)
    return os.path.basename(basepath)


class PopupTestCase(PopupBaseTestCase):
    """ Test the popup view """

    def test_variables(self):
        fieldname = 'multiRef2'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)
        popup = self._getPopup()
        relfield = self.obj.getField(fieldname)

        assert popup.at_url == '/plone/layer1/layer2/ref'
        assert popup.fieldName == fieldname
        assert popup.fieldRealName == fieldname
        assert popup.search_text == ''
        assert popup.field == relfield
        assert popup.multiValued == 1
        assert popup.search_index == relfield.widget.default_search_index
        assert popup.allowed_types == ()
        assert popup.at_obj == self.obj
        assert popup.filtered_indexes == ['Description', 'SearchableText']

        assert getPTName(popup.template.default_template.filename) == 'popup'

    def test_alternatetemplate(self):
        alternate_template = named_template_adapter(
            ViewPageTemplateFile('sample.pt'))
        zope.component.provideAdapter(alternate_template,
                                      adapts=(BrowserView, ),
                                      provides=INamedTemplate,
                                      name='alternate')
        fieldname = 'multiRef2'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)

        field = self.obj.getField(fieldname)
        field.widget.popup_name = 'alternate'

        popup = self._getPopup()
        assert getPTName(popup.template.default_template.filename) == 'sample'
        delattr(field.widget, 'popup_name')

    def test_close_window(self):
        # close popup after inserting a single reference
        fieldname = 'singleRef'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)
        popup = self._getPopup()
        assert popup.close_window == 1

        # don't close popup after inserting a multivalued reference
        fieldname = 'multiRef3'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)
        popup = self._getPopup()
        assert popup.close_window == 0

        # close popup after inserting a  multivalued reference, if forced
        fieldname = 'multiRef2'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)
        popup = self._getPopup()
        assert popup.close_window == 1

    def test_query(self):
        # normal query
        fieldname = 'multiRef3'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)
        self.request.set('search_index', 'getId')
        self.request.set('searchValue', 'news')
        popup = self._getPopup()
        batch = popup.getResult()
        assert isinstance(batch, Batch)
        assert len(batch) == 1
        assert batch[0].getObject() == self.portal.news
        assert popup.has_queryresults

    def test_path_query(self):
        # querying by path
        fieldname = 'multiRef3'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)
        self.request.set('search_index', 'getId')
        self.request.set('searchValue', 'path:/plone/events')
        popup = self._getPopup()
        batch = popup.getResult()
        assert isinstance(batch, Batch)
        # expected to have both the folder at "path" and its contents
        assert len(batch) == 2
        assert batch[0].getObject() == self.portal.events
        assert batch[1].getObject() == self.portal.events.aggregator
        assert popup.has_queryresults

    def test_noquery(self):
        # no query
        fieldname = 'multiRef3'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)
        self.request.set('search_index', 'getId')
        self.request.set('searchValue', '')
        popup = self._getPopup()
        batch = popup.getResult()
        assert isinstance(batch, Batch)
        assert len(batch) == 1
        assert batch[0].getObject() == self.obj
        assert popup.has_queryresults

    def test_title_or_id(self):
        fieldname = 'singleRef'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)
        popup = self._getPopup()
        catalog = getToolByName(self.portal, 'portal_catalog')

        # id
        refbrain = catalog(id='ref')[0]
        assert popup.title_or_id(refbrain) == 'ref'

        # title
        self.obj.setTitle('Lorem Ipsum')
        self.obj.reindexObject()

        refbrain = catalog(id='ref')[0]
        assert popup.title_or_id(refbrain) == 'Lorem Ipsum'

    def test_preview_url(self):
        fieldname = 'singleRef'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)
        popup = self._getPopup()

        catalog = getToolByName(self.portal, 'portal_catalog')
        brain = catalog(id='ref')[0]
        assert popup.preview_url(brain) == brain.getURL()

        # now testing what URL is get for content's where "/view" if forced
        site_properties = self.portal.portal_properties.site_properties
        site_properties.typesUseViewActionInListings = ('RefBrowserDemo',)
        assert popup.preview_url(brain) == brain.getURL()+'/view'

    def test_at_url(self):
        makeContent(self.folder, portal_type='RefBrowserDemo', id='with space')
        obj = self.folder['with space']
        fieldname = 'singleRef'
        self.request.set('at_url', '/plone/layer1/layer2/with space')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)
        popup = self._getPopup(obj=obj)
        self.assertEqual(popup.at_url, '/plone/layer1/layer2/with%20space')

    def test_subsite_query(self):
        """searches should not be restricted to subsites"""
        self.loginAsPortalOwner()
        self.portal.invokeFactory('Document', 'welcome-site')
        self.portal.invokeFactory('Folder', 'subsite')
        subsite = self.portal.subsite
        subsite.invokeFactory('Document', 'welcome-subsite')
        zope.interface.alsoProvides(subsite, INavigationRoot)

        self.request.set('SearchableText', 'welcome')
        results = subsite.restrictedTraverse('@@refbrowser_querycatalog')()
        # content outside subsite should also be returned
        self.assertTrue(len(results) > 1)


class PopupBreadcrumbTestCase(PopupBaseTestCase):
    """ Test the popup breadcrumbs """

    pat = ('http://nohost/plone%%srefbrowser_popup?fieldName=%s&'
           'fieldRealName=%s&at_url=/plone/layer1/layer2/ref')

    def test_breadcrumbs(self):
        """ Standard breadcrumbs """
        fieldname = 'multiRef3'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)
        popup = self._getPopup()
        bc = popup.breadcrumbs()

        path = ''
        pat = self.pat % (fieldname, fieldname)
        for compare, bc in zip([('', 'Home'),
                                ('layer1', 'Layer1'),
                                ('layer2', 'Layer2'),
                                ('ref', 'ref')], bc):
            path += compare[0] + '/'
            assert bc['absolute_url'] == pat % path
            assert bc['Title'] == compare[1]

    def test_startup(self):
        """A completely different startup dir.
        """
        fieldname = 'multiRef3'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)
        popup = self._getPopup(obj=self.portal.news)
        bc = popup.breadcrumbs()
        self.assertEqual(len(bc), 2)
        self.assertEqual(bc[0]['Title'], 'Home')
        self.assertEqual(bc[1]['Title'], 'News')

    def test_restrictedbrowsing(self):
        """ Only browse startup-dir and below """
        fieldname = 'multiRef3'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)

        widget = self.folder.ref.getField(fieldname).widget
        widget.restrict_browsing_to_startup_directory = 1

        popup = self._getPopup(obj=self.portal.layer1.layer2)
        widget.startup_directory = 'layer1/layer2'
        bc = popup.breadcrumbs()
        self.assertEqual(len(bc), 1)
        self.assertEqual(bc[0]['Title'], 'Layer2')

        widget.restrict_browsing_to_startup_directory = 0

    def test_isNotSelf(self):
        catalog = getToolByName(self.portal, 'portal_catalog')

        fieldname = 'multiRef3'
        self.request.set('at_url', '/plone/layer1/layer2/ref')
        self.request.set('fieldName', fieldname)
        self.request.set('fieldRealName', fieldname)

        clip = self.folder.manage_copyObjects('ref')
        self.folder.manage_pasteObjects(clip)

        copy = self.folder['copy_of_ref']
        copy.reindexObject()

        refbrain = catalog(id='ref')[0]
        copybrain = catalog(id='copy_of_ref')[0]

        popup = self._getPopup()
        assert popup.isNotSelf(copybrain) is True
        assert popup.isNotSelf(refbrain) is False


class HelperViewTestCase(TestCase):
    """ Test the helper view """

    def afterSetUp(self):
        self.createDefaultStructure()

    def test_interface(self):
        zope.interface.verify.verifyClass(IReferenceBrowserHelperView,
                                          ReferenceBrowserHelperView)

    def test_portalpath(self):
        helper = ReferenceBrowserHelperView(self.folder, self.app.REQUEST)
        self.assertEqual(helper.getPortalPath(), '/plone')

    def test_startupdirectory(self):
        makeContent(self.folder, portal_type='RefBrowserDemo', id='ref')
        context = self.folder.ref

        request = self.app.REQUEST

        field = context.getField('multiRef5')
        helper = ReferenceBrowserHelperView(context, request)

        # no query
        self.assertEqual(helper.getStartupDirectory(field),
                         'http://nohost/plone/layer1/layer2/ref')

        # string query
        field.widget.startup_directory = 'layer2'
        self.assertEqual(helper.getStartupDirectory(field),
                         'http://nohost/plone/layer1/layer2')

        # test base query is restricted on startup directory
        self.assertFalse('path' in field.widget.getBaseQuery(context, field))
        field.widget.restrict_browsing_to_startup_directory = 1
        self.assertTrue('path' in field.widget.getBaseQuery(context, field))
        self.assertEqual(field.widget.getBaseQuery(context, field)['path'],
                         '/plone/layer1/layer2')

        field.widget.startup_directory = 'layer1'
        self.assertEqual(field.widget.getBaseQuery(context, field)['path'],
                         '/plone/layer1')

        field.widget.startup_directory = '/foo/constant'
        self.assertEqual(helper.getStartupDirectory(field),
                         'http://nohost/plone/foo/constant')

        # dynamic query
        field.widget.startup_directory_method = 'dynamicDirectory'
        self.assertEqual(helper.getStartupDirectory(field),
                         'http://nohost/plone/bar/dynamic')

        # constant query
        field.widget.startup_directory_method = 'constantDirectory'
        self.assertEqual(helper.getStartupDirectory(field),
                         'http://nohost/plone/foo/constant')

        # clean up
        field.widget.startup_directory_method = ''

    def test_valuefromrequest_multi(self):
        """ If the request provides UIDs take these, not the references
            on the object for the edit-view of the widget.
        """
        makeContent(self.folder, portal_type='Document', id='doc1')
        makeContent(self.folder, portal_type='Document', id='doc2')
        makeContent(self.folder, portal_type='Document', id='doc3')

        context = self.folder.doc1
        request = TestRequest()
        helper = ReferenceBrowserHelperView(context, request)
        field = context.getField('relatedItems')

        # no relations
        self.assertEqual(helper.getFieldRelations(field), [])

        # relations on the object
        context.setRelatedItems(self.folder.doc3)
        self.assertEqual(helper.getFieldRelations(field),
                         [self.folder.doc3])

        # relations from the parameter (request, session, ...)
        uid = self.folder.doc2.UID()
        self.assertEqual(helper.getFieldRelations(field, [uid]),
                         [self.folder.doc2])

        # invalid values
        self.assertEqual(helper.getFieldRelations(field, 1), [])

    def test_valuefromrequest_single(self):
        makeContent(self.folder, portal_type='RefBrowserDemo', id='ref')
        makeContent(self.folder, portal_type='Document', id='doc2')
        makeContent(self.folder, portal_type='Document', id='doc3')

        context = self.folder.ref
        request = TestRequest()
        field = context.getField('singleRef')
        helper = ReferenceBrowserHelperView(context, request)

        # no relations
        self.assertEqual(helper.getFieldRelations(field), [])

        # relations on the object
        context.setSingleRef(self.folder.doc3)
        self.assertEqual(helper.getFieldRelations(field),
                         [self.folder.doc3])

        # relations from the parameter (request, session, ...)
        uid = self.folder.doc2.UID()
        self.assertEqual(helper.getFieldRelations(field, uid),
                         [self.folder.doc2])

    def test_getaturl(self):
        context = DummyObject('/plone/layer1/layer2')
        request = TestRequest()
        helper = ReferenceBrowserHelperView(context, request)
        self.assertEqual(helper.getAtURL(), '/plone/layer1/layer2')

        context = DummyObject('/plone/layer1/with space')
        helper = ReferenceBrowserHelperView(context, request)
        self.assertEqual(helper.getAtURL(), '/plone/layer1/with%20space')

    def test_getUidFromReference_fallback_to_UID(self):
        _marker = object()
        class DummyRef(object):
            def UID(self):
                return _marker
        helper = ReferenceBrowserHelperView(DummyObject('/plone/foo'), TestRequest())
        self.assertTrue(helper.getUidFromReference(DummyRef()) is _marker)

    def test_canview(self):
        makeContent(self.folder, portal_type='Document', id='doc1')
        request = TestRequest()
        helper = ReferenceBrowserHelperView(self.portal, request)
        self.assertTrue(helper.canView(self.folder.doc1))
        self.logout()
        self.assertFalse(helper.canView(self.folder.doc1))


class IntegrationTestCase(FunctionalTestCase):
    """ Browser/publish tests of referencebrowser widget
    """

    def afterSetUp(self):
        self.setRoles(['Manager'])
        makeContent(self.portal, portal_type='RefBrowserDemo', id='demo1')
        makeContent(self.portal, portal_type='Document', id='page1')
        makeContent(self.portal, portal_type='Folder', id='folder1')
        self.demo1_url = self.portal.demo1.absolute_url(1)
        self.popup_url = '%s/refbrowser_popup' % self.demo1_url

    def test_multivalued(self):
        """ We want to support `multiValued=True/False` on fields,
            but need `1` or `0` for our widget, since we work with
            javascript there.
        """
        context = self.portal.demo1

        # this is the easy case
        field = context.getField('singleRef')
        field.multiValued = 0

        response = self.publish(context.absolute_url(1) + '/base_edit',
                                self.basic_auth)
        self.assert_(
            'class="destructive removereference" value="Clear reference" data-fieldname="singleRef" data-multivalued="0"'
            in response.getBody())

        # we want to support this as well
        field = context.getField('singleRef')
        field.multiValued = False

        response = self.publish(context.absolute_url(1) + '/base_edit',
                                self.basic_auth)
        # this should be the same
        self.assert_(
            'class="destructive removereference" value="Clear reference" data-fieldname="singleRef" data-multivalued="0"'
            in response.getBody())

    def test_basewidget(self):
        response = self.publish('%s/base_edit' % self.demo1_url,
                                self.basic_auth)
        body = normalize(response.getBody())
        assert ('<script type="text/javascript" charset="iso-8859-1" '
                'src="http://nohost/plone/referencebrowser.js"> '
                '</script>') in body

        # Check the div.  Allow for the existence of extra classes and
        # extra data attributes.
        widgetdiv = re.compile((
            r'<div class="field ArchetypesReferenceBrowserWidget [^"]*"[^>]*'
            'id="archetypes-fieldname-singleRef"'))
        assert widgetdiv.search(body)
        assert (
            '<input id="ref_browser_singleRef_label" size="50" type="text" readonly="readonly" '
            'value="No reference set. Click the add button to select." /> '
            ) in body
        assert ('<input type="hidden" name="singleRef" id="ref_browser_singleRef" /> ') in body
        assert ('<input type="button" class="searchButton addreference" '
                'value="Add..." src="') in body
        assert '''<input type="button" class="destructive removereference" value="Clear reference" data-fieldname="singleRef" data-multivalued="0" />''' in body

    def getNormalizedPopup(self, url=None, field=None, startup_path=None):
        if url is None:
            url = self.demo1_url
        if field is None:
            field = 'singleRef'
        if startup_path is None:
            startup_path = self.popup_url
        response = self.publish(
            '%s?fieldName=%s&fieldRealName=%s&at_url=%s'
            % (startup_path, field, field, url), self.basic_auth)

        return normalize(response.getBody())

    def test_quoted_url(self):
        makeContent(self.portal, portal_type='RefBrowserDemo', id='spaced demo')
        url = self.portal['spaced demo'].absolute_url(1)
        body = self.getNormalizedPopup(url)
        assert '<input type="hidden" name="at_url" value="plone/spaced%20demo" />' in body

    def test_popup_html(self):
        body = self.getNormalizedPopup()
        assert '''<body class="popup atrefbrowser" id="atrefbrowserpopup"''' in body

        assert '<input type="hidden" name="fieldName" value="singleRef" />' in body
        assert '<input type="hidden" name="fieldRealName" value="singleRef" />' in body
        assert '<input type="hidden" name="at_url" value="plone/demo1" />' in body

    def test_popup_items(self):
        wanted_insertlinks = 2

        body = self.getNormalizedPopup()
        INSERTLINK = re.compile(r'<input type="checkbox" class="insertreference" id="[0-9a-f]*?" rel="[0-9a-f]*?" />')
        INSERTLINK_UUID = re.compile(r'<input type="checkbox" class="insertreference" id="[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}" rel="[\w]{8}-[\w]{4}-[\w]{4}-[\w]{4}-[\w]{12}" />')

        ROWS = re.compile(r'<tr.*?>(.*?)</tr>', re.MULTILINE|re.DOTALL)
        if HAS_DASH_UUID:
            self.assertEqual(len(INSERTLINK_UUID.findall(body)), wanted_insertlinks)
        else:
            self.assertEqual(len(INSERTLINK.findall(body)), wanted_insertlinks)

        makeContent(self.portal, portal_type='News Item', id='newsitem')
        body = self.getNormalizedPopup()

        if HAS_DASH_UUID:
            self.assertEqual(len(INSERTLINK_UUID.findall(body)), wanted_insertlinks)
        else:
            self.assertEqual(len(INSERTLINK.findall(body)), wanted_insertlinks)

    def test_bc_navigationroot(self):
        makeContent(self.portal.folder1, portal_type='Document', id='page1')

        page = self.portal.folder1.page1

        browser = Browser()
        data = {
            'fieldName': 'relatedItems',
            'fieldRealName': 'relatedItems',
            'at_url': page.absolute_url(1)}

        basic = '%s:%s' % (portal_owner, default_password)

        browser.addHeader('Authorization', 'Basic %s' % basic)
        browser.open('%s/refbrowser_popup?%s' % (page.absolute_url(),
                                                 urlencode(data)))
        self.assertTrue(('<a class="browsesite" href="http://nohost/plone/refbrowser_popup?'
                         'fieldName=relatedItems&amp;fieldRealName=relatedItems'
                         '&amp;at_url=plone/folder1/page1" rel="Home"> '
                         '<span>Home</span> </a>')
                        in normalize(browser.contents))

        # now let's change the navigation root
        zope.interface.alsoProvides(self.portal.folder1, INavigationRoot)
        browser.open('%s/refbrowser_popup?%s' % (page.absolute_url(),
                                                 urlencode(data)))
        self.assertTrue(('<a class="browsesite" href="http://nohost/plone/folder1/refbrowser_popup?'
                         'fieldName=relatedItems&amp;fieldRealName=relatedItems'
                         '&amp;at_url=plone/folder1/page1" rel="Home"> '
                         '<span>Home</span> </a>')
                        in normalize(browser.contents))

    def test_startup_directory(self):
        startup_path = self.portal.folder1.absolute_url(1)
        body = self.getNormalizedPopup(startup_path=startup_path,
                                       field='multiRef3')
        self.assertTrue(
            ('<div id="portal-breadcrumbs"> '
             '<span id="breadcrumbs-you-are-here">You are here:</span> '
             '<span id="breadcrumbs-home"> '
             '<a href="http://nohost/plone">Home</a> '
             '<span class="breadcrumbSeparator"> / </span> '
             '</span> '
             '<span id="breadcrumbs-1" dir="ltr"> '
             '<span id="breadcrumbs-current">folder1</span> '
             '</span> '
             '</div>') in body)


def test_suite():
    return unittest.TestSuite([
        unittest.makeSuite(ProductsTestCase),
        unittest.makeSuite(PopupTestCase),
        unittest.makeSuite(PopupBreadcrumbTestCase),
        unittest.makeSuite(HelperViewTestCase),
        unittest.makeSuite(IntegrationTestCase),
        ])
