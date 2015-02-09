from unittest import defaultTestLoader
from Products.Archetypes.interfaces import IImageField
from Products.ATContentTypes.content.image import ATImageSchema, ATImage
from plone.app.imaging.tests.base import ImagingTestCase
from plone.app.imaging.monkey import getAvailableSizes


class MonkeyPatchTests(ImagingTestCase):

    def afterSetUp(self):
        self.image = ATImage('test')
        self.field = self.image.getField('image')
        self.sizes = ATImageSchema['image'].sizes   # save original value

    def beforeTearDown(self):
        ATImageSchema['image'].sizes = self.sizes   # restore original value

    def testAvailableSizes(self):
        # make sure the field was patched
        self.assertEqual(self.field.getAvailableSizes.func_code,
            getAvailableSizes.func_code)
        # set custom image sizes and check the helper
        iprops = self.portal.portal_properties.imaging_properties
        iprops.manage_changeProperties(allowed_sizes=['foo 23:23', 'bar 8:8'])
        self.assertEqual(self.field.getAvailableSizes(self.image),
            dict(foo = (23, 23), bar = (8, 8)))

    def testAvailableSizesInstanceMethod(self):
        marker = dict(foo=23)
        def foo(self):
            return marker
        ATImage.foo = foo                       # create new instance method
        ATImageSchema['image'].sizes = 'foo'    # restore original value
        self.assertEqual(self.field.getAvailableSizes(self.image), marker)

    def testAvailableSizesCallable(self):
        def foo():
            return 'foo!'
        ATImageSchema['image'].sizes = foo      # store method in schema
        self.assertEqual(self.field.getAvailableSizes(self.image), 'foo!')

    def testAvailableSizesOnField(self):
        marker = dict(foo=23)
        ATImageSchema['image'].sizes = marker   # store dict in schema
        self.assertEqual(self.field.getAvailableSizes(self.image), marker)


class RegistryTests(ImagingTestCase):

    def testImageFieldInterface(self):
        data = self.getImage()
        folder = self.folder
        image = folder[folder.invokeFactory('Image', id='foo', image=data)]
        field = image.getField('image')
        self.assertTrue(IImageField.providedBy(field))


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
