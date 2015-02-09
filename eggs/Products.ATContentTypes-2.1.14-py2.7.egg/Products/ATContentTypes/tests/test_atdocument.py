import unittest

from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase, atctftestcase

import transaction
from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes import atapi
from Products.ATContentTypes.tests.utils import dcEdit

from Products.ATContentTypes.content.document import ATDocument
from Products.ATContentTypes.lib.validators import TidyHtmlWithCleanupValidator
from Products.ATContentTypes.tests.utils import NotRequiredTidyHTMLValidator
from Products.ATContentTypes.tests.utils import input_file_path
from Products.ATContentTypes.interfaces import IHistoryAware
from Products.ATContentTypes.interfaces import ITextContent
from Products.ATContentTypes.interfaces import IATDocument
from zope.interface.verify import verifyObject
from cgi import FieldStorage
from Products.ATContentTypes import config as atct_config
from ZPublisher.HTTPRequest import FileUpload

example_stx = """
Header

 Text, Text, Text

   * List
   * List
"""

example_rest = """
Header
======

Text, text, text

* List
* List
"""


def editATCT(obj):
    text_format = 'text/structured'
    dcEdit(obj)
    obj.setText(example_stx, mimetype=text_format)

tests = []


class TestSiteATDocument(atcttestcase.ATCTTypeTestCase):

    klass = ATDocument
    portal_type = 'Document'
    title = 'Page'
    meta_type = 'ATDocument'

    def test_doesImplementHistoryAware(self):
        iface = IHistoryAware
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_implementsTextContent(self):
        iface = ITextContent
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_implementsATDocument(self):
        iface = IATDocument
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_edit(self):
        new = self._ATCT
        editATCT(new)

    def test_cmf_edit_failure(self):
        self._ATCT.edit(thisisnotcmfandshouldbeignored=1)

    def test_rename_keeps_contenttype(self):
        doc = self._ATCT
        doc.setText(example_rest, mimetype="text/x-rst")
        self.assertTrue(str(doc.getField('text').getContentType(doc)) == "text/x-rst")
        #make sure we have _p_jar
        transaction.savepoint(optimistic=True)

        cur_id = 'ATCT'
        new_id = 'WasATCT'
        self.folder.manage_renameObject(cur_id, new_id)
        doc = getattr(self.folder, new_id)
        field = doc.getField('text')
        self.assertTrue(str(field.getContentType(doc)) == "text/x-rst")

    def test_x_safe_html(self):
        doc = self._ATCT
        mimetypes = (
            ('text/html', '<p>test</p>'),
            # MTR doens't know about text/stx, and transforming
            # doubles the tags. Yuck.
            ('text/structured', '<p><p>test</p></p>\n'),
            # XXX
            # ('text/x-rst', ("<p>&lt;p&gt;test&lt;/p&gt;&lt;script&gt;"
            #                 "I'm a nasty boy&lt;p&gt;nested&lt;/p&gt;"
            #                 "&lt;/script&gt;</p>\n")),
            # ('text/python-source', '<p>test</p>'),
            # XXX
            # ('text/plain', ("<p>&lt;p&gt;test&lt;/p&gt;&lt;script&gt;"
            #                 "I'm a nasty boy&lt;p&gt;nested&lt;/p&gt;"
            #                 "&lt;/script&gt;</p>\n")),
            )
        for mimetype, expected in mimetypes:
            # scrub html is removing unallowed tags
            text = "<p>test</p><script>I'm a nasty boy<p>nested</p></script>"
            doc.setText(text, mimetype=mimetype)
            txt = doc.getText()
            self.assertEqual(txt, expected, (txt, expected, mimetype))

    def test_get_size(self):
        atct = self._ATCT
        editATCT(atct)
        self.assertEqual(atct.get_size(), len(example_stx))

    if atct_config.HAS_MX_TIDY:
        # this test is null and void if mx.Tidy isn't even installed

        def test_tidy_validator_with_upload_wrong_encoding(self):
            doc = self._ATCT

            field = doc.getField('text')
            request = self.app.REQUEST
            setattr(request, 'text_text_format', 'text/html')
            input_file_name = 'tidy1-in.html'
            in_file = open(input_file_path(input_file_name))
            env = {'REQUEST_METHOD': 'PUT'}
            headers = {'content-type': 'text/html',
                       'content-length': len(in_file.read()),
                       'content-disposition': 'attachment; filename=%s' % input_file_name}
            in_file.seek(0)
            fs = FieldStorage(fp=in_file, environ=env, headers=headers)
            f = FileUpload(fs)

            tcv = TidyHtmlWithCleanupValidator('tidy_validator_with_cleanup')
            result = tcv.__call__(f, field=field, REQUEST=request)

            self.assertEqual(result, 1)

            expected_file = open(input_file_path('tidy1-out.html'))
            expected = expected_file.read()
            expected_file.close()
            self.assertEqual(request['text_tidier_data'], expected)

tests.append(TestSiteATDocument)


class TestATDocumentFields(atcttestcase.ATCTFieldTestCase):

    def afterSetUp(self):
        atcttestcase.ATCTFieldTestCase.afterSetUp(self)
        self._dummy = self.createDummy(klass=ATDocument)

    def test_text_field_mutator_filename(self):
        dummy = self._dummy
        field = dummy.getField('text')
        mutator = field.getMutator(dummy)
        self.assertEqual(field.getFilename(dummy), None)
        self.assertEqual(field.getContentType(dummy), 'text/html')
        mutator('', filename='foo.txt')
        self.assertEqual(field.getFilename(dummy), 'foo.txt')
        self.assertEqual(field.getContentType(dummy), 'text/plain')

    def test_text_field_mutator_mime(self):
        dummy = self._dummy
        field = dummy.getField('text')
        mutator = field.getMutator(dummy)
        self.assertEqual(field.getFilename(dummy), None)
        self.assertEqual(field.getContentType(dummy), 'text/html')
        mutator('', mimetype='text/plain')
        self.assertEqual(field.getFilename(dummy), None)
        self.assertEqual(field.getContentType(dummy), 'text/plain')

    def test_text_field_mutator_none_mime(self):
        dummy = self._dummy
        field = dummy.getField('text')
        mutator = field.getMutator(dummy)
        self.assertEqual(field.getFilename(dummy), None)
        self.assertEqual(field.getContentType(dummy), 'text/html')
        mutator('', mimetype=None)
        self.assertEqual(field.getFilename(dummy), None)
        self.assertEqual(field.getContentType(dummy), 'text/plain')

    def test_text_field_mutator_none_filename(self):
        dummy = self._dummy
        field = dummy.getField('text')
        mutator = field.getMutator(dummy)
        self.assertEqual(field.getFilename(dummy), None)
        self.assertEqual(field.getContentType(dummy), 'text/html')
        mutator('', filename=None)
        self.assertEqual(field.getFilename(dummy), None)
        self.assertEqual(field.getContentType(dummy), 'text/plain')

    def test_text_setEmptyText(self):
        dummy = self._dummy
        field = dummy.getField('text')

        # set text to a non-trivial value
        mutator = field.getMutator(dummy)
        mutator('Hello World!')

        # now, set an empty text
        mutator('')

        # verify that text is indeed empty
        accessor = field.getAccessor(dummy)
        self.assertEqual(accessor(), '')

    def test_textField(self):
        dummy = self._dummy
        field = dummy.getField('text')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 0, 'Value is %s' % field.required)
        self.assertTrue(field.default == '', 'Value is %s' % str(field.default))
        self.assertTrue(field.searchable == 1, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'getText',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setText',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission == ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'text', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AnnotationStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AnnotationStorage(migrate=True),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.validators == NotRequiredTidyHTMLValidator,
                        'Value is %s' % repr(field.validators))
        self.assertTrue(isinstance(field.widget, atapi.RichWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))

        self.assertTrue(field.primary == 1, 'Value is %s' % field.primary)
        self.assertTrue(field.default_content_type is None,
                        'Value is %s' % field.default_content_type)
        self.assertTrue(field.default_output_type == 'text/x-html-safe',
                        'Value is %s' % field.default_output_type)

        self.assertTrue('text/html' in field.getAllowedContentTypes(dummy))

tests.append(TestATDocumentFields)


class TestATDocumentFunctional(atctftestcase.ATCTIntegrationTestCase):

    portal_type = 'Document'
    views = ('document_view', )

    def test_id_change_on_initial_edit(self):
        """Make sure Id is taken from title on initial edit and not otherwise"""
        # first create an object using the createObject script

        response = self.publish(self.folder_path +
                                '/createObject?type_name=%s' % self.portal_type,
                                self.basic_auth)

        self.assertEqual(response.getStatus(), 302)  # Redirect to edit

        location = response.getHeader('Location')
        self.assertTrue(location.startswith(self.folder_url), location)
        self.assertTrue(location.endswith('edit'), location)

        # Perform the redirect
        edit_form_path = location[len(self.app.REQUEST.SERVER_URL):]
        response = self.publish(edit_form_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)  # OK

        #Change the title
        temp_id = location.split('/')[-2]
        obj_title = "New Title for Object"
        new_id = "new-title-for-object"
        new_obj = getattr(self.folder.aq_explicit, temp_id)
        new_obj_path = '/%s' % new_obj.absolute_url(1)
        self.assertEqual(new_obj.checkCreationFlag(), True)  # object is not yet edited

        response = self.publish('%s/atct_edit?form.submitted=1&title=%s&text=Blank' % (new_obj_path, obj_title,), self.basic_auth)  # Edit object
        self.assertEqual(response.getStatus(), 302)  # OK
        self.assertEqual(new_obj.getId(), new_id)  # does id match
        self.assertEqual(new_obj.checkCreationFlag(), False)  # object is fully created
        new_title = "Second Title"
        response = self.publish('%s/atct_edit?form.submitted=1&title=%s&text=Blank' % ('/%s' % new_obj.absolute_url(1), new_title,), self.basic_auth)  # Edit object
        self.assertEqual(response.getStatus(), 302)  # OK
        self.assertEqual(new_obj.getId(), new_id)  # id shouldn't have changed

tests.append(TestATDocumentFunctional)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
