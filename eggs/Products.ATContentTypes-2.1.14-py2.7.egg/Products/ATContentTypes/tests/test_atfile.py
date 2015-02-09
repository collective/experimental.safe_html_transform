# -*- coding: utf-8 -*-

import unittest
from Testing import ZopeTestCase  # side effect import. leave it here.
from Products.ATContentTypes.tests import atcttestcase, atctftestcase

from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes import atapi
from Products.ATContentTypes.tests.utils import dcEdit
import StringIO

from plone.app.blob.content import ATBlob
from Products.ATContentTypes.interfaces import IATFile
from Products.ATContentTypes.interfaces import IFileContent
from zope.interface.verify import verifyObject


file_text = """
foooooo
"""


def editATCT(obj):
    dcEdit(obj)
    obj.edit(file=file_text)


class Fakefile(StringIO.StringIO):
    pass


tests = []


class TestSiteATFile(atcttestcase.ATCTTypeTestCase):

    klass = ATBlob
    portal_type = 'File'
    title = 'File'
    meta_type = 'ATFile'

    def test_implementsFileContent(self):
        iface = IFileContent
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_implementsATFile(self):
        iface = IATFile
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_edit(self):
        new = self._ATCT
        editATCT(new)

    def testCompatibilityFileAccess(self):
        new = self._ATCT
        editATCT(new)
        # test for crappy access ways of CMF :)
        self.assertEqual(str(new), file_text)
        self.assertEqual(new.data, file_text)
        self.assertEqual(str(new.getFile()), file_text)
        self.assertEqual(new.getFile().data, file_text)
        self.assertEqual(new.get_data(), file_text)

    def testCompatibilityContentTypeAccess(self):
        new = self._ATCT
        editATCT(new)
        # TODO: more tests

    def test_schema_marshall(self):
        atct = self._ATCT
        schema = atct.Schema()
        marshall = schema.getLayerImpl('marshall')
        marshallers = [atapi.PrimaryFieldMarshaller]
        try:
            from Products.Marshall import ControlledMarshaller
            marshallers.append(ControlledMarshaller)
        except ImportError:
            pass
        self.assertTrue(isinstance(marshall, tuple(marshallers)), marshall)

    def testInvokeFactoryWithFileContents(self):
        # test for Plone tracker #4939
        fakefile = Fakefile()
        fakefile.filename = 'some-filename'
        id = self.folder.invokeFactory(self.portal_type,
                                       'image.2005-11-18.4066860572',
                                       file=fakefile)
        self.assertEqual(id, fakefile.filename)

    def testUpperCaseFilename(self):
        fakefile = Fakefile()
        fakefile.filename = 'Some-filename-With-Uppercase.txt'
        id = 'file.2005-11-18.4066860573'
        self.folder.invokeFactory(self.portal_type, id)
        self.folder[id].setFile(fakefile)
        self.assertFalse(id in self.folder)
        self.assertTrue(fakefile.filename in self.folder)

    def testUpperCaseFilenameWithFunnyCharacters(self):
        fakefile = Fakefile()
        fakefile.filename = 'Zope&Plo?ne .txt'
        id = 'file.2005-11-18.4066860574'
        self.folder.invokeFactory(self.portal_type, id)
        self.folder[id].setFile(fakefile)
        self.assertFalse(id in self.folder)
        self.assertTrue('Zope-Plo-ne .txt' in self.folder)

    def testWindowsUploadFilename(self):
        fakefile = Fakefile()
        fakefile.filename = 'c:\\Windows\\Is\\Worthless\\file.txt'
        id = 'file.2005-11-18.4066860574'
        self.folder.invokeFactory(self.portal_type, id)
        self.folder[id].setFile(fakefile)
        self.assertFalse(id in self.folder)
        self.assertFalse(fakefile.filename in self.folder)
        self.assertTrue('file.txt' in self.folder)

    def testWindowsDuplicateFiles(self):
        fakefile = Fakefile()
        fakefile.filename = 'c:\\Windows\\Is\\Worthless\\file.txt'
        id = 'file.2005-11-18.4066860574'
        self.folder.invokeFactory(self.portal_type, id)
        self.folder[id].setFile(fakefile)
        self.folder.invokeFactory(self.portal_type, id)
        request = self.folder.REQUEST
        request.form['id'] = id
        request.form['file_file'] = fakefile
        errors = {}
        self.folder[id].post_validate(request, errors)
        self.assertTrue('file' in errors)

tests.append(TestSiteATFile)


class TestATFileFields(atcttestcase.ATCTFieldTestCase):

    # Title is not a required field, since we don't require them
    # on File/Image - they are taken from the filename if not present.
    # "Add the comment 'damn stupid fucking test'" -- optilude ;)
    def test_title(self):
        pass

    def afterSetUp(self):
        atcttestcase.ATCTFieldTestCase.afterSetUp(self)
        self._dummy = self.createDummy(klass=ATBlob, subtype='File')

    def test_fileField(self):
        dummy = self._dummy
        field = dummy.getField('file')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 1, 'Value is %s' % field.required)
        self.assertFalse(field.default, 'Value is %s' % str(field.default))
        self.assertTrue(field.searchable == True, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'getFile',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setFile',
                        'Value is %s' % field.mutator)
        self.assertTrue(field.read_permission == View,
                        'Value is %s' % field.read_permission)
        self.assertTrue(field.write_permission == ModifyPortalContent,
                        'Value is %s' % field.write_permission)
        self.assertTrue(field.generateMode == 'veVc',
                        'Value is %s' % field.generateMode)
        self.assertTrue(field.force == '', 'Value is %s' % field.force)
        self.assertTrue(field.type == 'blob', 'Value is %s' % field.type)
        self.assertTrue(isinstance(field.storage, atapi.AnnotationStorage),
                        'Value is %s' % type(field.storage))
        self.assertTrue(field.getLayerImpl('storage') == atapi.AnnotationStorage(migrate=True),
                        'Value is %s' % field.getLayerImpl('storage'))
        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.validators == "(('isNonEmptyFile', V_REQUIRED), ('checkFileMaxSize', V_REQUIRED))",
                        'Value is %s' % str(field.validators))
        self.assertTrue(isinstance(field.widget, atapi.FileWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))
        self.assertTrue(field.primary == 1, 'Value is %s' % field.primary)

tests.append(TestATFileFields)


class TestCleanupFilename(atcttestcase.ATCTSiteTestCase):

    def test_cleanup_filename(self):
        self.app.REQUEST.set('HTTP_ACCEPT_LANGUAGE', 'el')
        from Products.ATContentTypes.content.base import cleanupFilename
        text = unicode('Νίκος Τζάνος', 'utf-8')
        self.assertEqual(cleanupFilename(text, request=self.app.REQUEST),
                          'Nikos Tzanos')

tests.append(TestCleanupFilename)


class TestATFileFunctional(atctftestcase.ATCTIntegrationTestCase):

    portal_type = 'File'
    views = ('file_view', 'download', )

    def test_inlineMimetypes_Office(self):
        # Only PDF and Office docs are shown inline
        self.obj.setFormat('application/msword')
        response = self.publish(self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Disposition'), None)

        self.obj.setFormat('application/x-msexcel')
        response = self.publish(self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Disposition'), None)

        self.obj.setFormat('application/vnd.ms-excel')
        response = self.publish(self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Disposition'), None)

        self.obj.setFormat('application/vnd.ms-powerpoint')
        response = self.publish(self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Disposition'), None)

    def test_inlineMimetypes_PDF(self):
        # Only PDF and Office docs are shown inline
        self.obj.setFormat('application/pdf')
        response = self.publish(self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Disposition'), None)

    def test_inlineMimetypes_Text(self):
        # Only PDF and Office docs are shown inline
        self.obj.setFilename('foo.txt')
        self.obj.setFormat('text/plain')
        response = self.publish(self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Disposition'), 'attachment; filename="foo.txt"')

    def test_inlineMimetypes_Binary(self):
        # Only PDF and Office docs are shown inline
        self.obj.setFilename('foo.exe')
        self.obj.setFormat('application/octet-stream')
        response = self.publish(self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getHeader('Content-Disposition'), 'attachment; filename="foo.exe"')

tests.append(TestATFileFunctional)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
