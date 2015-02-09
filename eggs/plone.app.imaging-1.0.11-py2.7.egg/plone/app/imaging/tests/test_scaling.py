from unittest import TestSuite, makeSuite
from plone.app.imaging.tests.base import ImagingTestCase
from plone.app.imaging.tests.base import ImagingFunctionalTestCase
from plone.app.imaging.traverse import ImageTraverser
from plone.app.imaging.traverse import DefaultImageScaleHandler
from StringIO import StringIO
from PIL.Image import open


class TraverseCounterMixin:

    def afterSetUp(self):
        self.counter = 0        # wrap `publishTraverse` with a counter
        self.original = ImageTraverser.publishTraverse
        def publishTraverse(adapter, request, name):
            self.counter += 1
            return self.original(adapter, request, name)
        ImageTraverser.publishTraverse = publishTraverse

    def beforeTearDown(self):
        ImageTraverser.publishTraverse = self.original


class ImageTraverseTests(TraverseCounterMixin, ImagingTestCase):

    def testImageThumb(self):
        data = self.getImage()
        folder = self.folder
        image = folder[folder.invokeFactory('Image', id='foo', image=data)]
        # make sure traversing works as is and with scaling
        traverse = folder.REQUEST.traverseName
        self.assertEqual(traverse(image, 'image').data, data)
        sizes = image.getField('image').getAvailableSizes(image)
        self.assertTrue('thumb' in sizes.keys())
        thumb = traverse(image, 'image_thumb')
        self.assertEqual(thumb.getContentType(), 'image/gif')
        self.assertEqual(thumb.data[:6], 'GIF87a')
        width, height = sizes['thumb']
        self.assertEqual(thumb.width, width)
        self.assertEqual(thumb.height, height)
        # also check the generated tag
        url = image.absolute_url() + '/image_thumb'
        tag = '<img src="%s" alt="foo" title="foo" height="%d" width="%d" />'
        self.assertEqual(thumb.tag(), tag % (url, height, width))
        # calling str(...) on the scale should return the tag
        self.assertEqual(str(thumb), thumb.tag())
        # make sure the traversal adapter was called in fact
        self.assertEqual(self.counter, 2)

    def testCustomSizes(self):
        data = self.getImage()
        folder = self.folder
        image = folder[folder.invokeFactory('Image', id='foo', image=data)]
        # set custom image sizes
        iprops = self.portal.portal_properties.imaging_properties
        iprops.manage_changeProperties(allowed_sizes=['foo 23:23', 'bar 6:8'])
        # make sure traversing works with the new sizes
        traverse = folder.REQUEST.traverseName
        foo = traverse(image, 'image_foo')
        self.assertEqual(foo.getContentType(), 'image/gif')
        self.assertEqual(foo.data[:6], 'GIF87a')
        self.assertEqual(foo.width, 23)
        self.assertEqual(foo.height, 23)
        # also check the generated tag
        url = image.absolute_url() + '/image_foo'
        tag = '<img src="%s" alt="foo" title="foo" height="23" width="23" />'
        self.assertEqual(foo.tag(), tag % url)
        # and the other specified size
        bar = traverse(image, 'image_bar')
        self.assertEqual(bar.getContentType(), 'image/gif')
        self.assertEqual(bar.data[:6], 'GIF87a')
        self.assertEqual(bar.width, 6)
        self.assertEqual(bar.height, 6)
        # make sure the traversal adapter was called in fact
        self.assertEqual(self.counter, 2)

    def testCustomSizesForNewsItems(self):
        # let's also check custom scales work for "News Item" content
        data = self.getImage()
        folder = self.folder
        newsitem = folder[folder.invokeFactory('News Item',
            id='newsitem', image=data)]
        # set custom image sizes
        iprops = self.portal.portal_properties.imaging_properties
        iprops.manage_changeProperties(allowed_sizes=['foo 23:23'])
        # make sure traversing works with the new sizes
        traverse = folder.REQUEST.traverseName
        foo = traverse(newsitem, 'image_foo')
        self.assertEqual(foo.getContentType(), 'image/gif')
        self.assertEqual(foo.data[:6], 'GIF87a')
        self.assertEqual(foo.width, 23)
        self.assertEqual(foo.height, 23)

    def testCustomSizesWithSpaces(self):
        data = self.getImage()
        folder = self.folder
        image = folder[folder.invokeFactory('Image', id='foo', image=data)]
        # set custom image sizes
        iprops = self.portal.portal_properties.imaging_properties
        iprops.manage_changeProperties(allowed_sizes=['foo bar 23:23'])
        # make sure traversing works with the new sizes
        traverse = folder.REQUEST.traverseName
        foo_bar = traverse(image, 'image_foo_bar')
        self.assertEqual(foo_bar.getContentType(), 'image/gif')
        self.assertEqual(foo_bar.data[:6], 'GIF87a')
        self.assertEqual(foo_bar.width, 23)
        self.assertEqual(foo_bar.height, 23)
        # also check the generated tag
        url = image.absolute_url() + '/image_foo_bar'
        tag = '<img src="%s" alt="foo" title="foo" height="23" width="23" />'
        self.assertEqual(foo_bar.tag(), tag % url)

    def testScaleInvalidation(self):
        data = self.getImage()
        folder = self.folder
        image = folder[folder.invokeFactory('Image', id='foo', image=data)]
        # first view the thumbnail of the original image
        traverse = folder.REQUEST.traverseName
        thumb1 = traverse(image, 'image_thumb')
        # now upload a new one and make sure the thumbnail has changed
        image.update(image=self.getImage('image.jpg'))
        traverse = folder.REQUEST.traverseName
        thumb2 = traverse(image, 'image_thumb')
        self.assertFalse(thumb1.data == thumb2.data, 'thumb not updated?')

    def testCustomSizeChange(self):
        data = self.getImage()
        folder = self.folder
        image = folder[folder.invokeFactory('Image', id='foo', image=data)]
        # set custom image sizes & view a scale
        iprops = self.portal.portal_properties.imaging_properties
        iprops.manage_changeProperties(allowed_sizes=['foo 23:23'])
        traverse = folder.REQUEST.traverseName
        foo = traverse(image, 'image_foo')
        self.assertEqual(foo.width, 23)
        self.assertEqual(foo.height, 23)
        # now let's update the scale dimensions, after which the scale
        # should still be the same...
        iprops.manage_changeProperties(allowed_sizes=['foo 42:42'])
        foo = traverse(image, 'image_foo')
        self.assertEqual(foo.width, 23)
        self.assertEqual(foo.height, 23)
        # we first need to trigger recreation of all scales...
        self.portal.portal_atct.recreateImageScales()
        foo = traverse(image, 'image_foo')
        self.assertEqual(foo.width, 42)
        self.assertEqual(foo.height, 42)
        # make sure the traversal adapter was call in fact
        self.assertEqual(self.counter, 3)


class ImagePublisherTests(TraverseCounterMixin, ImagingFunctionalTestCase):

    def testPublishThumb(self):
        data = self.getImage()
        folder = self.folder
        folder.invokeFactory('Image', id='foo', image=data)
        # make sure traversing works as is and with scaling
        base = '/'.join(folder.getPhysicalPath())
        credentials = self.getCredentials()
        # first the image itself...
        response = self.publish(base + '/foo', basic=credentials)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), data)
        self.assertEqual(response.getHeader('Content-Type'), 'image/gif')
        # then the field without a scale name
        response = self.publish(base + '/foo/image', basic=credentials)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), data)
        self.assertEqual(response.getHeader('Content-Type'), 'image/gif')
        # and last a scaled version
        response = self.publish(base + '/foo/image_thumb', basic=credentials)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody()[:6], 'GIF87a')
        self.assertEqual(response.getHeader('Content-Type'), 'image/gif')
        # make sure the traversal adapter was call in fact
        self.assertEqual(self.counter, 9)

    def testPublishCustomSize(self):
        data = self.getImage()
        folder = self.folder
        folder.invokeFactory('Image', id='foo', image=data)
        # set custom image sizes
        iprops = self.portal.portal_properties.imaging_properties
        iprops.manage_changeProperties(allowed_sizes=['foo 23:23'])
        # make sure traversing works as expected
        base = '/'.join(folder.getPhysicalPath())
        credentials = self.getCredentials()
        response = self.publish(base + '/foo/image_foo', basic=credentials)
        self.assertEqual(response.getStatus(), 200)
        foo = open(StringIO(response.getBody()))
        self.assertEqual(foo.format, 'GIF')
        self.assertEqual(foo.size, (23, 23))
        # make sure the traversal adapter was call in fact
        self.assertEqual(self.counter, 3)


class DefaultAdapterTests(ImagingTestCase):

    def afterSetUp(self):
        data = self.getImage()
        folder = self.folder
        self.image = folder[folder.invokeFactory('Image', id='foo', image=data)]
        self.field = self.image.getField('image')
        self.handler = DefaultImageScaleHandler(self.field)
        iprops = self.portal.portal_properties.imaging_properties
        iprops.manage_changeProperties(allowed_sizes=['foo 60:60'])

    def testCreateScale(self):
        foo = self.handler.createScale(self.image, 'foo', 100, 80)
        self.assertEqual(foo['id'], 'image_foo')
        self.assertEqual(foo['content_type'], 'image/gif')
        self.assertEqual(foo['data'][:6], 'GIF87a')

    def testCreateScaleWithZeroWidth(self):
        foo = self.handler.createScale(self.image, 'foo', 100, 0)
        self.assertEqual(foo, None)

    def testCreateScaleWithoutData(self):
        folder = self.folder
        image = folder[folder.invokeFactory('Image', id='image')]
        field = image.getField('image')
        handler = DefaultImageScaleHandler(field)
        foo = handler.createScale(image, 'foo', 100, 80)
        self.assertEqual(foo, None)

    def testGetScale(self):
        foo = self.handler.getScale(self.image, 'foo')
        self.assertEqual(foo.getId(), 'image_foo')
        self.assertEqual(foo.getContentType(), 'image/gif')
        self.assertEqual(foo.data[:6], 'GIF87a')
        self.assertEqual(foo.width, 60)
        self.assertEqual(foo.height, 60)

    def testGetUnknownScale(self):
        foo = self.handler.getScale(self.image, 'foo?')
        self.assertEqual(foo, None)

    def testScaleThatCausesErrorsCanBeSuppressed(self):
        def causeError(*args, **kwargs):
            raise Exception
        self.field.scale = causeError
        self.field.swallowResizeExceptions = False
        self.assertRaises(Exception, self.handler.getScale, self.image, 'foo')
        # scaling exceptions should be "swallowed" when set on the field...
        self.field.swallowResizeExceptions = True
        self.assertEqual(self.handler.getScale(self.image, 'foo'), None)


def test_suite():
    return TestSuite([
        makeSuite(ImageTraverseTests),
        makeSuite(ImagePublisherTests),
        makeSuite(DefaultAdapterTests),
    ])
