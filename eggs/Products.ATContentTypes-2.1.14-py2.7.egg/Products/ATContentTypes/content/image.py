from zope.interface import implements

from Products.CMFCore.permissions import View
from Products.CMFCore.permissions import ModifyPortalContent
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from ComputedAttribute import ComputedAttribute

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import ImageField
from Products.Archetypes.atapi import ImageWidget
from Products.Archetypes.atapi import PrimaryFieldMarshaller
from Products.Archetypes.atapi import AnnotationStorage

from Products.ATContentTypes.config import PROJECTNAME
from Products.ATContentTypes.configuration import zconf
from Products.ATContentTypes.content.base import registerATCT
from Products.ATContentTypes.content.base import ATCTFileContent
from Products.ATContentTypes.content.schemata import ATContentTypeSchema
from Products.ATContentTypes.content.schemata import finalizeATCTSchema
from Products.ATContentTypes.interfaces import IATImage

from Products.ATContentTypes.lib.imagetransform import ATCTImageTransform

from Products.ATContentTypes import ATCTMessageFactory as _

from Products.validation.config import validation
from Products.validation.validators.SupplValidators import MaxSizeValidator
from Products.validation import V_REQUIRED

validation.register(MaxSizeValidator('checkImageMaxSize',
                                     maxsize=zconf.ATImage.max_file_size))


ATImageSchema = ATContentTypeSchema.copy() + Schema((
    ImageField('image',
               required=True,
               primary=True,
               languageIndependent=True,
               storage=AnnotationStorage(migrate=True),
               swallowResizeExceptions=zconf.swallowImageResizeExceptions.enable,
               pil_quality=zconf.pil_config.quality,
               pil_resize_algo=zconf.pil_config.resize_algo,
               max_size=zconf.ATImage.max_image_dimension,
               sizes={'large': (768, 768),
                      'preview': (400, 400),
                      'mini': (200, 200),
                      'thumb': (128, 128),
                      'tile': (64, 64),
                      'icon': (32, 32),
                      'listing': (16, 16),
                     },
               validators=(('isNonEmptyFile', V_REQUIRED),
                           ('checkImageMaxSize', V_REQUIRED)),
               widget=ImageWidget(
                        description='',
                        label=_(u'label_image', default=u'Image'),
                        show_content_type=False,)),

    ), marshall=PrimaryFieldMarshaller()
    )

# Title is pulled from the file name if we don't specify anything,
# so it's not strictly required, unlike in the rest of ATCT.
ATImageSchema['title'].required = False

finalizeATCTSchema(ATImageSchema)


class ATImage(ATCTFileContent, ATCTImageTransform):
    """An image, which can be referenced in documents or displayed in an album."""

    schema = ATImageSchema

    portal_type = 'Image'
    archetype_name = 'Image'
    _atct_newTypeFor = {'portal_type': 'CMF Image', 'meta_type': 'Portal Image'}
    assocMimetypes = ('image/*', )
    assocFileExt = ('jpg', 'jpeg', 'png', 'gif', )
    cmf_edit_kws = ('file', )

    implements(IATImage)

    security = ClassSecurityInfo()

    def exportImage(self, format, width, height):
        return '', ''

    security.declareProtected(ModifyPortalContent, 'setImage')
    def setImage(self, value, refresh_exif=True, **kwargs):
        """Set ID to uploaded file name if Title is empty."""
        # set exif first because rotation might screw up the exif data
        # the exif methods can handle str, Pdata, OFSImage and file
        # like objects
        self.getEXIF(value, refresh=refresh_exif)
        self._setATCTFileContent(value, **kwargs)

    def _should_set_id_to_filename(self, filename, title):
        """If title is blank, have the caller set my ID to the uploaded file's name."""
        # When the title is blank, sometimes the filename is returned as the title.
        return filename == title or not title

    security.declareProtected(View, 'tag')
    def tag(self, **kwargs):
        """Generate image tag using the api of the ImageField
        """
        return self.getField('image').tag(self, **kwargs)

    def __str__(self):
        """cmf compatibility
        """
        return self.tag()

    security.declareProtected(View, 'get_size')
    def get_size(self):
        """ZMI / Plone get size method

        BBB: ImageField.get_size() returns the size of the original image + all
        scales but we want only the size of the original image.
        """
        img = self.getImage()
        if not getattr(aq_base(img), 'get_size', False):
            return 0
        return img.get_size()

    security.declareProtected(View, 'getSize')
    def getSize(self, scale=None):
        field = self.getField('image')
        return field.getSize(self, scale=scale)

    security.declareProtected(View, 'getWidth')
    def getWidth(self, scale=None):
        return self.getSize(scale)[0]

    security.declareProtected(View, 'getHeight')
    def getHeight(self, scale=None):
        return self.getSize(scale)[1]

    width = ComputedAttribute(getWidth, 1)
    height = ComputedAttribute(getHeight, 1)

    security.declarePrivate('cmf_edit')
    def cmf_edit(self, precondition='', file=None, title=None):
        if file is not None:
            self.setImage(file)
        if title is not None:
            self.setTitle(title)
        self.reindexObject()

    def __bobo_traverse__(self, REQUEST, name):
        """Transparent access to image scales
        """
        if name.startswith('image'):
            field = self.getField('image')
            image = None
            if name == 'image':
                image = field.getScale(self)
            else:
                scalename = name[len('image_'):]
                if scalename in field.getAvailableSizes(self):
                    image = field.getScale(self, scale=scalename)
            if image is not None and not isinstance(image, basestring):
                # image might be None or '' for empty images
                return image

        return ATCTFileContent.__bobo_traverse__(self, REQUEST, name)

registerATCT(ATImage, PROJECTNAME)
