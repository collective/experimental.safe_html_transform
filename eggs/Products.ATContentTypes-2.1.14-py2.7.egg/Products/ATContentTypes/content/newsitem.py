from zope.interface import implements

from AccessControl import ClassSecurityInfo

from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import ImageField
from Products.Archetypes.atapi import StringField
from Products.Archetypes.atapi import TextField
from Products.Archetypes.atapi import ImageWidget
from Products.Archetypes.atapi import RichWidget
from Products.Archetypes.atapi import StringWidget
from Products.Archetypes.atapi import RFC822Marshaller
from Products.Archetypes.atapi import AnnotationStorage

from Products.ATContentTypes.config import PROJECTNAME
from Products.ATContentTypes.configuration import zconf
from Products.ATContentTypes.content.base import registerATCT
from Products.ATContentTypes.content.base import translateMimetypeAlias
from Products.ATContentTypes.content.document import ATDocumentBase
from Products.ATContentTypes.content.image import ATCTImageTransform
from Products.ATContentTypes.content.schemata import ATContentTypeSchema
from Products.ATContentTypes.content.schemata import finalizeATCTSchema
from Products.ATContentTypes.interfaces import IATNewsItem

from Products.ATContentTypes import ATCTMessageFactory as _

from Products.CMFCore.permissions import View

from Products.validation.config import validation
from Products.validation.validators.SupplValidators import MaxSizeValidator
from Products.validation import V_REQUIRED

validation.register(MaxSizeValidator('checkNewsImageMaxSize',
                                     maxsize=zconf.ATNewsItem.max_file_size))


ATNewsItemSchema = ATContentTypeSchema.copy() + Schema((
    TextField('text',
        required=False,
        searchable=True,
        primary=True,
        storage=AnnotationStorage(migrate=True),
        validators=('isTidyHtmlWithCleanup',),
        #validators=('isTidyHtml',),
        default_output_type='text/x-html-safe',
        widget=RichWidget(
            description='',
            label=_(u'label_body_text', u'Body Text'),
            rows=25,
            allow_file_upload=zconf.ATDocument.allow_document_upload)
        ),

    ImageField('image',
        required=False,
        storage=AnnotationStorage(migrate=True),
        languageIndependent=True,
        max_size=zconf.ATNewsItem.max_image_dimension,
        sizes={'large': (768, 768),
               'preview': (400, 400),
               'mini': (200, 200),
               'thumb': (128, 128),
               'tile': (64, 64),
               'icon': (32, 32),
               'listing': (16, 16),
              },
        validators=(('isNonEmptyFile', V_REQUIRED),
                    ('checkNewsImageMaxSize', V_REQUIRED)),
        widget=ImageWidget(
            description=_(u'help_news_image', default=u'Will be shown in the news listing, and in the news item itself. Image will be scaled to a sensible size.'),
            label=_(u'label_news_image', default=u'Image'),
            show_content_type=False)
        ),

    StringField('imageCaption',
        required=False,
        searchable=True,
        widget=StringWidget(
            description='',
            label=_(u'label_image_caption', default=u'Image Caption'),
            size=40)
        ),
    ), marshall=RFC822Marshaller()
    )

ATNewsItemSchema['description'].widget.label = \
    _(u'label_summary', default=u'Summary')

finalizeATCTSchema(ATNewsItemSchema)


class ATNewsItem(ATDocumentBase, ATCTImageTransform):
    """An announcement that will show up on the news portlet and in the news listing."""

    schema = ATNewsItemSchema

    portal_type = 'News Item'
    archetype_name = 'News Item'
    _atct_newTypeFor = {'portal_type': 'CMF News Item', 'meta_type': 'News Item'}
    assocMimetypes = ()
    assocFileExt = ('news', )
    cmf_edit_kws = ATDocumentBase.cmf_edit_kws

    implements(IATNewsItem)

    security = ClassSecurityInfo()

    security.declareProtected(View, 'tag')
    def tag(self, **kwargs):
        """Generate image tag using the api of the ImageField
        """
        if 'title' not in kwargs:
            kwargs['title'] = self.getImageCaption()
        return self.getField('image').tag(self, **kwargs)

    security.declarePrivate('cmf_edit')
    def cmf_edit(self, text, description=None, text_format=None, **kwargs):
        if description is not None:
            self.setDescription(description)
        self.setText(text, mimetype=translateMimetypeAlias(text_format))
        self.update(**kwargs)

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

        return ATDocumentBase.__bobo_traverse__(self, REQUEST, name)

registerATCT(ATNewsItem, PROJECTNAME)
