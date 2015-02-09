# -*- coding: utf-8 -*-

import unittest

from cStringIO import StringIO
import os

from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes import atapi
from plone.app.blob.content import ATBlob
from Products.ATContentTypes.interfaces import IImageContent
from Products.ATContentTypes.interfaces import IATImage
from Products.ATContentTypes.tests import atcttestcase, atctftestcase
from Products.ATContentTypes.tests.utils import dcEdit, PACKAGE_HOME
from Products.PloneTestCase.PloneTestCase import FunctionalTestCase, setupPloneSite
from Testing import ZopeTestCase  # side effect import. leave it here.
from zope.interface.verify import verifyObject

# BBB Zope 2.12
try:
    from Testing.testbrowser import Browser
except ImportError:
    from Products.Five.testbrowser import Browser

# third party extension
import exif


def loadImage(name, size=0):
    """Load image from testing directory
    """
    path = os.path.join(PACKAGE_HOME, 'input', name)
    fd = open(path, 'rb')
    data = fd.read()
    fd.close()
    return data

TEST_EXIF_ERROR = loadImage('canoneye.jpg')
TEST_GIF = loadImage('test.gif')
TEST_GIF_LEN = len(TEST_GIF)
TEST_DIV_ERROR = loadImage('divisionerror.jpg')
TEST_JPEG_FILE = open(os.path.join(PACKAGE_HOME, 'input', 'canoneye.jpg'), 'rb')
# XXX replace it by an image with exif informations but w/o
# the nasty error ...
TEST_JPEG = loadImage('canoneye.jpg')
TEST_JPEG_LEN = len(TEST_JPEG)


def editATCT(obj):
    obj.setImage(TEST_GIF, content_type="image/gif")
    dcEdit(obj)

tests = []


setupPloneSite()


class TestIDFromTitle(FunctionalTestCase):
    """Browsertests to make sure ATImages derive their default IDs from their titles"""
    # TODO: Merge into TestATImageFunctional, below.

    def afterSetUp(self):
        self.userId = 'fred'
        self.password = 'secret'
        self.portal.acl_users.userFolderAddUser(self.userId, self.password, ['Manager'], [])
        self.browser = Browser()
        self._log_in()

    def _log_in(self):
        """Log in as someone who can add new Images."""
        self.browser.open(self.portal.absolute_url())
        self.browser.getLink('Log in').click()
        self.browser.getControl('Login Name').value = self.userId
        self.browser.getControl('Password').value = self.password
        self.browser.getControl('Log in').click()

    def _make_image(self, title, filename='canoneye.jpg'):
        """Add a new Image at the root of the Plone site."""
        self.browser.open(self.portal.absolute_url() + '/createObject?type_name=Image')
        self.browser.getControl('Title').value = title
        image = self.browser.getControl(name='image_file')
        image.filename = filename
        TEST_JPEG_FILE.seek(0)
        image.value = TEST_JPEG_FILE
        self.browser.getControl('Save').click()

    def test_image_id_from_filename_and_title(self):
        # Get ID from filename:
        self._make_image('')
        self.assertTrue('canoneye.jpg' in self.browser.url)

        # Get ID from title.
        # As a side effect, make sure the ID validator doesn't overzealously
        # deny our upload of something else called canoneye.jpg, even though
        # we're not going to compute its ID from its filename.
        self._make_image('Wonderful Image')
        self.assertTrue('/wonderful-image' in self.browser.url)

    def test_image_id_from_unicode_title(self):
        self._make_image('', filename=u'Pictüre 1.png'.encode('utf-8'))
        normalized = 'Picture%201.png'
        self.assertTrue(normalized in self.browser.url)

tests.append(TestIDFromTitle)


class TestSiteATImage(atcttestcase.ATCTTypeTestCase):

    klass = ATBlob
    portal_type = 'Image'
    title = 'Image'
    meta_type = 'ATImage'

    def test_implementsImageContent(self):
        iface = IImageContent
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_implementsATImage(self):
        iface = IATImage
        self.assertTrue(iface.providedBy(self._ATCT))
        self.assertTrue(verifyObject(iface, self._ATCT))

    def test_edit(self):
        new = self._ATCT
        editATCT(new)

    def test_getEXIF(self):
        # NOTE: not a real test
        exif_data = self._ATCT.getEXIF()
        self.assertTrue(isinstance(exif_data, dict), type(exif_data))

    def test_exifOrientation(self):
        # NOTE: not a real test
        r, m = self._ATCT.getEXIFOrientation()

    def test_transform(self):
        self._ATCT.update(image=TEST_GIF)
        # NOTE: not a real test
        self._ATCT.transformImage(2)

    def test_autotransform(self):
        # NOTE: not a real test
        self._ATCT.autoTransformImage()

    def test_broken_pil(self):
        # PIL has a nasty bug when the image ratio is too extrem like 300x15:
        # Module PIL.Image, line 1136, in save
        # Module PIL.PngImagePlugin, line 510, in _save
        # Module PIL.ImageFile, line 474, in _save
        # SystemError: tile cannot extend outside image
        atct = self._ATCT

        # test upload
        atct.setImage(TEST_GIF, mimetype='image/gif', filename='test.gif')
        self.assertEqual(atct.getImage().data, TEST_GIF)

    def test_division_by_0_pil(self):
        # pil generates a division by zero error on some images
        atct = self._ATCT

        # test upload
        atct.setImage(TEST_DIV_ERROR, mimetype='image/jpeg',
                      filename='divisionerror.jpg')
        self.assertEqual(atct.getImage().data, TEST_DIV_ERROR)

    def test_get_size(self):
        atct = self._ATCT
        editATCT(atct)
        self.assertEqual(len(TEST_GIF), TEST_GIF_LEN)
        self.assertEqual(atct.get_size(), TEST_GIF_LEN)

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

    def test_dcEdit(self):
        new = self._ATCT
        new.setImage(TEST_GIF, content_type="image/gif")
        dcEdit(new)

    def test_broken_exif(self):
        # This test fails even with the 2005.05.12 exif version from
        #    http://home.cfl.rr.com/genecash/
        f = StringIO(TEST_EXIF_ERROR)
        exif_data = exif.process_file(f, debug=False)
        # probably want to add some tests on returned data. Currently gives
        #  ValueError in process_file

    def test_exif_upload(self):
        atct = self._ATCT
        atct._image_exif = None

        # string upload
        atct.setImage(TEST_JPEG)
        self.assertTrue(len(atct.getEXIF()), atct.getEXIF())
        atct._image_exif = None

        # file upload
        atct.setImage(TEST_JPEG_FILE)
        self.assertTrue(len(atct.getEXIF()), atct.getEXIF())
        atct._image_exif = None

        # Pdata upload
        from OFS.Image import Pdata
        pd = Pdata(TEST_JPEG)
        atct.setImage(pd)
        self.assertTrue(len(atct.getEXIF()), atct.getEXIF())
        atct._image_exif = None

        # ofs image upload
        ofs = atct.getImage()
        atct.setImage(ofs)
        self.assertTrue(len(atct.getEXIF()), atct.getEXIF())
        atct._image_exif = None

tests.append(TestSiteATImage)


class TestATImageFields(atcttestcase.ATCTFieldTestCase):

    # Title is not a required field, since we don't require them
    # on File/Image - they are taken from the filename if not present.
    # "Add the comment 'damn stupid fucking test'" -- optilude ;)
    def test_title(self):
        pass

    def afterSetUp(self):
        atcttestcase.ATCTFieldTestCase.afterSetUp(self)
        self._dummy = self.createDummy(klass=ATBlob, subtype='Image')

    def test_imageField(self):
        dummy = self._dummy
        field = dummy.getField('image')

        self.assertTrue(ILayerContainer.providedBy(field))
        self.assertTrue(field.required == 1, 'Value is %s' % field.required)
        self.assertTrue(field.default == None, 'Value is %s' % str(field.default))
        self.assertTrue(field.searchable == 0, 'Value is %s' % field.searchable)
        self.assertTrue(field.vocabulary == (),
                        'Value is %s' % str(field.vocabulary))
        self.assertTrue(field.enforceVocabulary == 0,
                        'Value is %s' % field.enforceVocabulary)
        self.assertTrue(field.multiValued == 0,
                        'Value is %s' % field.multiValued)
        self.assertTrue(field.isMetadata == 0, 'Value is %s' % field.isMetadata)
        self.assertTrue(field.accessor == 'getImage',
                        'Value is %s' % field.accessor)
        self.assertTrue(field.mutator == 'setImage',
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
        self.assertTrue(field.validators == "(('isNonEmptyFile', V_REQUIRED), ('checkImageMaxSize', V_REQUIRED))",
                        'Value is %s' % str(field.validators))
        self.assertTrue(isinstance(field.widget, atapi.ImageWidget),
                        'Value is %s' % id(field.widget))
        vocab = field.Vocabulary(dummy)
        self.assertTrue(isinstance(vocab, atapi.DisplayList),
                        'Value is %s' % type(vocab))
        self.assertTrue(tuple(vocab) == (), 'Value is %s' % str(tuple(vocab)))
        self.assertTrue(field.primary == 1, 'Value is %s' % field.primary)

tests.append(TestATImageFields)


class TestATImageFunctional(atctftestcase.ATCTIntegrationTestCase):

    portal_type = 'Image'
    views = ('image_view', 'download', 'atct_image_transform')

    def afterSetUp(self):
        atctftestcase.ATCTIntegrationTestCase.afterSetUp(self)
        self.obj.setImage(TEST_GIF, content_type="image/gif")
        dcEdit(self.obj)

    def test_url_returns_image(self):
        response = self.publish(self.obj_path, self.basic_auth)
        self.assertEqual(response.getStatus(), 200)  # OK

    def test_bobo_hook_security(self):
        # Make sure that users with 'View' permission can use the
        # bobo_traversed image scales, even if denied to anonymous
        response1 = self.publish(self.obj_path + '/image', self.basic_auth)
        self.assertEqual(response1.getStatus(), 200)  # OK
        # deny access to anonymous
        self.obj.manage_permission('View', ['Manager', 'Member'], 0)
        response2 = self.publish(self.obj_path + '/image', self.basic_auth)
        # Should be allowed for member
        self.assertEqual(response2.getStatus(), 200)  # OK
        # Should fail for anonymous
        response3 = self.publish(self.obj_path + '/image')
        self.assertEqual(response3.getStatus(), 302)
        bobo_exception = response3.getHeader('bobo-exception-type')
        self.assertTrue('Unauthorized' in bobo_exception)

tests.append(TestATImageFunctional)


def test_suite():
    suite = unittest.TestSuite()
    for test in tests:
        suite.addTest(unittest.makeSuite(test))
    return suite
