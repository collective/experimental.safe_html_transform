from Products.Archetypes.atapi import BaseSchema
from Products.Archetypes.atapi import MetadataSchema
from Products.Archetypes.atapi import ReferenceField
from Products.Archetypes.atapi import BooleanField
from Products.Archetypes.atapi import BooleanWidget
from Products.ATContentTypes import ATCTMessageFactory as _
from Products.CMFCore.permissions import ModifyPortalContent

from archetypes.referencebrowserwidget import ReferenceBrowserWidget

# for ATContentTypes we want to have the description in the edit view
# just like CMF
ATContentTypeSchema = BaseSchema.copy() + MetadataSchema((
    BooleanField('excludeFromNav',
        required=False,
        languageIndependent=True,
        schemata='metadata',  # moved to 'default' for folders
        widget=BooleanWidget(
            description=_(u'help_exclude_from_nav', default=u'If selected, this item will not appear in the navigation tree'),
            label=_(u'label_exclude_from_nav', default=u'Exclude from navigation'),
            visible={'view': 'hidden',
                     'edit': 'visible'},
            ),
        ),
    ),)

ATContentTypeSchema['id'].searchable = True
ATContentTypeSchema['id'].validators = ('isValidId',)

# Update the validation layer after change the validator in runtime
ATContentTypeSchema['id']._validationLayer()

ATContentTypeSchema['description'].schemata = 'default'

# BBB
ATContentTypeBaseSchema = ATContentTypeSchema

relatedItemsField = ReferenceField('relatedItems',
        relationship='relatesTo',
        multiValued=True,
        isMetadata=True,
        languageIndependent=False,
        index='KeywordIndex',
        referencesSortable=True,
        keepReferencesOnCopy=True,
        write_permission=ModifyPortalContent,
        widget=ReferenceBrowserWidget(
            allow_search=True,
            allow_browse=True,
            allow_sorting=True,
            show_indexes=False,
            force_close_on_insert=True,
            label=_(u'label_related_items', default=u'Related Items'),
            description='',
            visible={'edit': 'visible', 'view': 'invisible'}
            )
        )
ATContentTypeSchema.addField(relatedItemsField.copy())

#Enabling next / previous navigation

NextPreviousAwareSchema = MetadataSchema((
    BooleanField('nextPreviousEnabled',
        #required=False,
        languageIndependent=True,
        schemata='metadata',
        widget=BooleanWidget(
            description=_(u'help_nextprevious', default=u'This enables next/previous widget on content items contained in this folder.'),
            label=_(u'label_nextprevious', default=u'Enable next previous navigation'),
            visible={'view': 'hidden',
                     'edit': 'visible'},
            ),
        default_method="getNextPreviousParentValue"
        ),
    ),)


def marshall_register(schema):
    try:
        # It's a soft dependency, if not available ignore it.
        from Products.Marshall import ControlledMarshaller
    except ImportError:
        return
    # If it's available, then wrap the existing marshaller with a
    # ControlledMarshaller.
    if not schema.hasLayer('marshall'):
        # We are not interested in schemas that don't have a marshaller.
        return

    # Get existing marshaller.
    marshaller = schema.getLayerImpl('marshall')
    # Check if not already wrapped.
    if isinstance(marshaller, ControlledMarshaller):
        return

    # Wrap into a ControlledMarshaller
    marshaller = ControlledMarshaller(marshaller)
    schema.registerLayer('marshall', marshaller)


def finalizeATCTSchema(schema, folderish=False, moveDiscussion=True):
    """Finalizes an ATCT type schema to alter some fields
    """
    schema.moveField('relatedItems', pos='bottom')
    if folderish:
        schema['relatedItems'].widget.visible['edit'] = 'invisible'
    schema.moveField('excludeFromNav', after='allowDiscussion')
    if moveDiscussion:
        schema.moveField('allowDiscussion', after='relatedItems')

    # Categorization
    if 'subject' in schema:
        schema.changeSchemataForField('subject', 'categorization')
    if 'relatedItems' in schema:
        schema.changeSchemataForField('relatedItems', 'categorization')
    if 'location' in schema:
        schema.changeSchemataForField('location', 'categorization')
    if 'language' in schema:
        schema.changeSchemataForField('language', 'categorization')

    # Dates
    if 'effectiveDate' in schema:
        schema.changeSchemataForField('effectiveDate', 'dates')
    if 'expirationDate' in schema:
        schema.changeSchemataForField('expirationDate', 'dates')
    if 'creation_date' in schema:
        schema.changeSchemataForField('creation_date', 'dates')
    if 'modification_date' in schema:
        schema.changeSchemataForField('modification_date', 'dates')

    # Creators
    if 'creators' in schema:
        schema.changeSchemataForField('creators', 'creators')
    if 'contributors' in schema:
        schema.changeSchemataForField('contributors', 'creators')
    if 'rights' in schema:
        schema.changeSchemataForField('rights', 'creators')

    # Settings
    if 'allowDiscussion' in schema:
        schema.changeSchemataForField('allowDiscussion', 'settings')
    if 'excludeFromNav' in schema:
        schema.changeSchemataForField('excludeFromNav', 'settings')
    if 'nextPreviousEnabled' in schema:
        schema.changeSchemataForField('nextPreviousEnabled', 'settings')

    marshall_register(schema)
    return schema

# Make sure the base ATCT schema is correctly finalized
finalizeATCTSchema(ATContentTypeSchema)

__all__ = ('ATContentTypeSchema', 'relatedItemsField',)
