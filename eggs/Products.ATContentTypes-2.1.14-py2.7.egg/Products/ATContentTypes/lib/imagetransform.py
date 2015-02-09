import logging
from cStringIO import StringIO

from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent
from AccessControl import ClassSecurityInfo
from ExtensionClass import Base
from DateTime import DateTime
from App.class_init import InitializeClass
from OFS.Image import Image as OFSImage
from OFS.Image import Pdata

from Products.ATContentTypes.configuration import zconf
from Products.ATContentTypes.config import HAS_PIL
from Products.ATContentTypes import ATCTMessageFactory as _

# third party extension
import exif

# the following code is based on the rotation code of Photo
if HAS_PIL:
    import PIL.Image

LOG = logging.getLogger('ATCT.image')

# transpose constants, taken from PIL.Image to maintain compatibilty
FLIP_LEFT_RIGHT = 0
FLIP_TOP_BOTTOM = 1
ROTATE_90 = 2
ROTATE_180 = 3
ROTATE_270 = 4


TRANSPOSE_MAP = {
    FLIP_LEFT_RIGHT: _(u'Flip around vertical axis'),
    FLIP_TOP_BOTTOM: _(u'Flip around horizontal axis'),
    ROTATE_270: _(u'Rotate 90 clockwise'),
    ROTATE_180: _(u'Rotate 180'),
    ROTATE_90: _(u'Rotate 90 counterclockwise'),
   }

AUTO_ROTATE_MAP = {
    0: None,
    90: ROTATE_270,
    180: ROTATE_180,
    270: ROTATE_90,
    }


class ATCTImageTransform(Base):
    """Base class for images containing transformation and exif functions

    * exif information
    * image rotation
    """

    security = ClassSecurityInfo()

    security.declarePrivate('getImageAsFile')
    def getImageAsFile(self, img=None, scale=None):
        """Get the img as file like object
        """
        if img is None:
            f = self.getField('image')
            img = f.getScale(self, scale)
        # img.data contains the image as string or Pdata chain
        data = None
        if isinstance(img, OFSImage):
            data = str(img.data)
        elif isinstance(img, Pdata):
            data = str(img)
        elif isinstance(img, str):
            data = img
        elif isinstance(img, file) or (hasattr(img, 'read') and
          hasattr(img, 'seek')):
            img.seek(0)
            return img
        if data:
            return StringIO(data)
        else:
            return None

    # image related code like exif and rotation
    # partly based on CMFPhoto

    security.declareProtected(View, 'getEXIF')
    def getEXIF(self, img=None, refresh=False):
        """Get the exif informations of the file

        The information is cached in _v_image_exif
        """
        cache = '_image_exif'

        if refresh:
            setattr(self, cache, None)

        exif_data = getattr(self, cache, None)

        if exif_data is None or not isinstance(exif_data, dict):
            io = self.getImageAsFile(img, scale=None)
            if io is not None:
                # some cameras are naughty :(
                try:
                    io.seek(0)
                    exif_data = exif.process_file(io, debug=False)
                except:
                    LOG.error('Failed to process EXIF information', exc_info=True)
                    exif_data = {}
                # seek to 0 and do NOT close because we might work
                # on a file upload which is required later
                io.seek(0)
                # remove some unwanted elements lik thumb nails
                for key in ('JPEGThumbnail', 'TIFFThumbnail',
                            'MakerNote JPEGThumbnail'):
                    if key in exif_data:
                        del exif_data[key]

        if not exif_data:
            # alawys return a dict
            exif_data = {}
        # set the EXIF cache even if the image has returned an empty
        # dict. This prevents regenerating the exif every time if an
        # image doesn't have exif information.
        setattr(self, cache, exif_data)
        return exif_data

    security.declareProtected(View, 'getEXIFOrientation')
    def getEXIFOrientation(self):
        """Get the rotation and mirror orientation from the EXIF data

        Some cameras are storing the informations about rotation and mirror in
        the exif data. It can be used for autorotation.
        """
        exif = self.getEXIF()
        mirror = 0
        rotation = 0
        code = exif.get('Image Orientation', None)

        if code is None:
            return (mirror, rotation)

        try:
            code = int(code)
        except ValueError:
            return (mirror, rotation)

        if code in (2, 4, 5, 7):
            mirror = 1
        if code in (1, 2):
            rotation = 0
        elif code in (3, 4):
            rotation = 180
        elif code in (5, 6):
            rotation = 90
        elif code in (7, 8):
            rotation = 270

        return (mirror, rotation)

    security.declareProtected(View, 'getEXIFOrigDate')
    def getEXIFOrigDate(self):
        """Get the EXIF DateTimeOriginal from the image (or None)
        """
        exif_data = self.getEXIF()
        raw_date = exif_data.get('EXIF DateTimeOriginal', None)
        if raw_date is not None:
            # some cameras are naughty ...
            try:
                return DateTime(str(raw_date))
            except:
                LOG.error('Failed to parse exif date %s' % raw_date, exc_info=True)
        return None

    security.declareProtected(ModifyPortalContent, 'transformImage')
    def transformImage(self, method, REQUEST=None):
        """
        Transform an Image:
            FLIP_LEFT_RIGHT
            FLIP_TOP_BOTTOM
            ROTATE_90 (rotate counterclockwise)
            ROTATE_180
            ROTATE_270 (rotate clockwise)
        """
        try:
            method = int(method)
        except ValueError:
            method = int(REQUEST.form.get('method'))
        if method not in TRANSPOSE_MAP:
            raise RuntimeError, "Unknown method %s" % method

        target = self.absolute_url() + '/atct_image_transform'

        if not HAS_PIL:
            if REQUEST:
                REQUEST.RESPONSE.redirect(target)

        image = self.getImageAsFile()
        image2 = StringIO()

        if image is not None:
            img = PIL.Image.open(image)
            del image
            fmt = img.format
            img = img.transpose(method)
            img.save(image2, fmt, quality=zconf.pil_config.quality)

            field = self.getField('image')
            mimetype = field.getContentType(self)
            filename = field.getFilename(self)

            # because AT tries to get mimetype and filename from a file like
            # object by attribute access I'm passing a string along
            self.setImage(image2.getvalue(), mimetype=mimetype,
                          filename=filename, refresh_exif=False)
            self.reindexObject()

        if REQUEST:
            REQUEST.RESPONSE.redirect(target)

    security.declareProtected(ModifyPortalContent, 'autoTransformImage')
    def autoTransformImage(self, REQUEST=None):
        """Auto transform image according to EXIF data

        Note: isn't using mirror
        """
        target = self.absolute_url() + '/atct_image_transform'
        mirror, rotation = self.getEXIFOrientation()
        transform = None
        if rotation:
            transform = AUTO_ROTATE_MAP.get(rotation, None)
            if transform is not None:
                self.transformImage(transform)
        if REQUEST:
            REQUEST.RESPONSE.redirect(target)
        else:
            return mirror, rotation, transform

    security.declareProtected(View, 'getTransformMap')
    def getTransformMap(self):
        """Get map for tranforming the image
        """
        return [{'name': n, 'value': v} for v, n in TRANSPOSE_MAP.items()]

    security.declareProtected(View, 'hasPIL')
    def hasPIL(self):
        """Is PIL installed?
        """
        return HAS_PIL

InitializeClass(ATCTImageTransform)
