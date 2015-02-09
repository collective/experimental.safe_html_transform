from Acquisition import aq_base
from cStringIO import StringIO
from logging import getLogger
from plone.app.imaging.interfaces import IImageScaleHandler
from plone.app.imaging.utils import getAllowedSizes, getQuality
from Products.Archetypes.Field import ImageField
from Products.Archetypes.utils import shasattr
from Products.ATContentTypes.content.image import ATImageSchema
from Products.ATContentTypes.content.newsitem import ATNewsItemSchema

logger = getLogger(__name__)

# Import conditionally, so we don't introduce a hard dependency
try:
    import PIL.Image
except ImportError:
    # no PIL, no scaled versions!
    logger.warning("Warning: no Python Imaging Libraries (PIL) found. "
                   "Archetypes based ImageFields don't scale if neccessary.")
else:
    pass


def getAvailableSizes(self, instance):
    """ get available sizes for scaled down images;  this uses the new,
        user-configurable settings, but still support instance methods
        and other callables;  see Archetypes/Field.py """
    sizes = getattr(aq_base(self), 'sizes', None)
    if isinstance(sizes, dict):
        return sizes
    elif isinstance(sizes, basestring):
        assert(shasattr(instance, sizes))
        method = getattr(instance, sizes)
        data = method()
        assert(isinstance(data, dict))
        return data
    elif callable(sizes):
        return sizes()
    else:
        sizes = getAllowedSizes()
        if sizes is None:
            sizes = self.original_getAvailableSizes(instance)
        return sizes


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


def scale(self, data, w, h, default_format='PNG'):
    """ use our quality setting as pil_quality """
    pil_quality = getQuality()

    #make sure we have valid int's
    size = int(w), int(h)

    original_file = StringIO(data)
    image = PIL.Image.open(original_file)

    if image.format == 'GIF' and size[0] >= image.size[0] \
            and size[1] >= image.size[1]:
        try:
            image.seek(image.tell() + 1)
            # original image is animated GIF and no bigger than the scale
            # requested
            # don't attempt to scale as this will lose animation
            original_file.seek(0)
            return original_file, 'gif'
        except EOFError:
            # image is not animated
            image.seek(0)

    # consider image mode when scaling
    # source images can be mode '1','L,','P','RGB(A)'
    # convert to greyscale or RGBA before scaling
    # preserve palletted mode (but not pallette)
    # for palletted-only image formats, e.g. GIF
    # PNG compression is OK for RGBA thumbnails
    original_mode = image.mode
    img_format = image.format and image.format or default_format
    if img_format in ('TIFF', 'EPS', 'PSD'):
        # non web image format have jpeg thumbnails
        target_format = 'JPEG'
    else:
        target_format = img_format

    if original_mode == '1':
        image = image.convert('L')
    elif original_mode == 'P':
        image = image.convert('RGBA')
    elif original_mode == 'CMYK':
        image = image.convert('RGBA')

    image.thumbnail(size, self.pil_resize_algo)
    # decided to only preserve palletted mode
    # for GIF, could also use image.format in ('GIF','PNG')
    if original_mode == 'P' and img_format == 'GIF':
        image = image.convert('P')
    thumbnail_file = StringIO()
    # quality parameter doesn't affect lossless formats
    image.save(thumbnail_file, target_format, quality=pil_quality, progressive=True)
    thumbnail_file.seek(0)
    return thumbnail_file, target_format.lower()


def patchImageField():
    """ monkey patch `ImageField` methods """
    ImageField.original_getAvailableSizes = ImageField.getAvailableSizes
    ImageField.getAvailableSizes = getAvailableSizes
    ImageField.original_createScales = ImageField.createScales
    ImageField.createScales = createScales
    ImageField.original_scale = ImageField.scale
    ImageField.scale = scale


def unpatchImageField():
    """ revert monkey patch regarding `ImageField` methods """
    ImageField.getAvailableSizes = ImageField.original_getAvailableSizes
    ImageField.createScales = ImageField.original_createScales
    ImageField.scale = ImageField.original_scale


def patchSchemas():
    """ monkey patch `sizes` attribute in `ATImageSchema` and
        `ATNewsItemSchema` to make it possible to detect whether the
        sizes has been overridden """
    ATImageSchema['image'].sizes = None
    ATNewsItemSchema['image'].sizes = None
