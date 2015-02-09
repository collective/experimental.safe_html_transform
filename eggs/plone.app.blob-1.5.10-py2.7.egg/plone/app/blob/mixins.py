from AccessControl import ClassSecurityInfo
from ComputedAttribute import ComputedAttribute
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.Archetypes.Field import ImageField
from Products.ATContentTypes.lib.imagetransform import ATCTImageTransform

from plone.app.imaging.interfaces import IImageScaleHandler
from plone.app.blob.utils import openBlob


class ImageFieldMixin(ImageField):
    """ mixin class for methods needed for image field """

    security = ClassSecurityInfo()

    security.declareProtected(View, 'getSize')
    def getSize(self, instance, scale=None):
        """ get size of scale or original """
        if scale is None:
            return self.getUnwrapped(instance).getSize()
        handler = IImageScaleHandler(self, None)
        if handler is not None:
            image = handler.getScale(instance, scale)
            if image is not None:
                return image.width, image.height
        return 0, 0

    security.declareProtected(View, 'getScale')
    def getScale(self, instance, scale=None, **kwargs):
        """ get scale by name or original """
        if scale is None:
            return self.getUnwrapped(instance, **kwargs)
        handler = IImageScaleHandler(self, None)
        if handler is not None:
            return handler.getScale(instance, scale)
        return None

    security.declareProtected(ModifyPortalContent, 'createScales')
    def createScales(self, instance, value=None):
        """ creates scales and stores them; largely based on the version from
            `Archetypes.Field.ImageField` """
        sizes = self.getAvailableSizes(instance)
        handler = IImageScaleHandler(self)
        for name, size in sizes.items():
            width, height = size
            data = handler.createScale(instance, name, width, height, data=value)
            if data is not None:
                handler.storeScale(instance, name, **data)


class ImageMixin(ATCTImageTransform):
    """ mixin class for methods needed for image content """

    cmf_edit_kws = ('file',)
    security = ClassSecurityInfo()

    # accessor and mutator methods

    security.declareProtected(View, 'getImage')
    def getImage(self, **kwargs):
        """ archetypes.schemaextender (wisely) doesn't mess with classes,
            so we have to provide our own accessor """
        return self.getBlobWrapper()

    security.declareProtected(ModifyPortalContent, 'setImage')
    def setImage(self, value, **kwargs):
        """ set image contents and possibly also the id """
        mutator = self.getField('image').getMutator(self)
        mutator(value, **kwargs)

    # methods from ATImage

    security.declareProtected(View, 'tag')
    def tag(self, **kwargs):
        """ generate image tag using the api of the ImageField """
        field = self.getField('image')
        if field is not None:
            return field.tag(self, **kwargs)

    security.declareProtected(View, 'getSize')
    def getSize(self, scale=None):
        field = self.getField('image')
        if field is not None:
            return field.getSize(self, scale=scale)

    security.declareProtected(View, 'getWidth')
    def getWidth(self, scale=None):
        size = self.getSize(scale)
        if size:
            return size[0]

    security.declareProtected(View, 'getHeight')
    def getHeight(self, scale=None):
        size = self.getSize(scale)
        if size:
            return size[1]

    width = ComputedAttribute(getWidth, 1)
    height = ComputedAttribute(getHeight, 1)

    # methods from ATCTImageTransform

    security.declarePrivate('getImageAsFile')
    def getImageAsFile(self, img=None, scale=None):
        """ get the img as file like object """
        if img is None:
            field = self.getField('image')
            img = field.getScale(self, scale)
        return openBlob(self.getBlobWrapper().getBlob())
