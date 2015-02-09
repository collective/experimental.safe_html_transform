# -*- coding: utf-8 -*-
from AccessControl import ClassSecurityInfo
from OFS.ObjectManager import ObjectManager
from archetypes.querywidget.field import QueryField
from archetypes.querywidget.widget import QueryWidget
from plone.app.contentlisting.interfaces import IContentListing
from Products.ATContentTypes.content import document, schemata
from Products.Archetypes import atapi
from Products.Archetypes.atapi import (BooleanField,
                                       BooleanWidget,
                                       IntegerField,
                                       LinesField,
                                       IntegerWidget,
                                       InAndOutWidget,
                                       StringField,
                                       StringWidget)
from Products.CMFCore.permissions import ModifyPortalContent, View
from Products.CMFCore.utils import getToolByName
from zope.interface import implements

from plone.app.collection import PloneMessageFactory as _
from plone.app.collection.config import ATCT_TOOLNAME, PROJECTNAME
from plone.app.collection.interfaces import ICollection


CollectionSchema = document.ATDocumentSchema.copy() + atapi.Schema((

    QueryField(
        name='query',
        widget=QueryWidget(
            label=_(u"Search terms"),
            description=_(u"Define the search terms for the items you want to "
                          u"list by choosing what to match on. "
                          u"The list of results will be dynamically updated."),
            ),
        validators=('javascriptDisabled',)
        ),

    StringField(
        name='sort_on',
        required=False,
        mode='rw',
        default='sortable_title',
        widget=StringWidget(
            label=_(u'Sort the collection on this index'),
            description='',
            visible=False,
            ),
        ),

    BooleanField(
        name='sort_reversed',
        required=False,
        mode='rw',
        default=False,
        widget=BooleanWidget(
            label=_(u'Sort the results in reversed order'),
            description='',
            visible=False,
            ),
        ),

    IntegerField(
        name='b_size',
        required=False,
        mode='rw',
        default=30,
        widget=IntegerWidget(
            label=_(u'Limit Results by Page'),
            description=_(u"Specify the number of items to show by page.")
            ),
        validators=('isInt',)
        ),

    IntegerField(
        name='limit',
        required=False,
        mode='rw',
        default=1000,
        widget=IntegerWidget(
            label=_(u'Limit Search Results'),
            description=_(u"Specify the maximum number of items to show.")
            ),
        validators=('isInt',)
        ),

    LinesField(
        name='customViewFields',
        required=False,
        mode='rw',
        default=('Title', 'Creator', 'Type', 'ModificationDate'),
        vocabulary='listMetaDataFields',
        enforceVocabulary=True,
        write_permission=ModifyPortalContent,
        widget=InAndOutWidget(
            label=_(u'Table Columns'),
            description=_(u"Select which fields to display when "
                          u"'Tabular view' is selected in the display menu.")
            ),
        ),
))

CollectionSchema.moveField('query', after='description')
if 'presentation' in CollectionSchema:
    CollectionSchema['presentation'].widget.visible = False
CollectionSchema['tableContents'].widget.visible = False


schemata.finalizeATCTSchema(
    CollectionSchema,
    folderish=False,
    moveDiscussion=False)


class Collection(document.ATDocument, ObjectManager):
    """A (new style) Plone Collection"""
    implements(ICollection)

    meta_type = "Collection"
    schema = CollectionSchema

    security = ClassSecurityInfo()

    # Override initializeArchetype to turn on syndication by default
    def initializeArchetype(self, **kwargs):
        ret_val = document.ATDocument.initializeArchetype(self, **kwargs)
        # Enable syndication by default
        syn_tool = getToolByName(self, 'portal_syndication', None)
        if syn_tool is not None:
            if (syn_tool.isSiteSyndicationAllowed() and
                                    not syn_tool.isSyndicationAllowed(self)):
                syn_tool.enableSyndication(self)
        return ret_val

    security.declareProtected(View, 'listMetaDataFields')
    def listMetaDataFields(self, exclude=True):
        """Return a list of metadata fields from portal_catalog.
        """
        tool = getToolByName(self, ATCT_TOOLNAME)
        return tool.getMetadataDisplay(exclude)

    security.declareProtected(View, 'results')
    def results(self, batch=True, b_start=0, b_size=0, sort_on=None, brains=False, custom_query={}):
        """Get results"""
        batch_size = self.getB_size()
        if sort_on is None:
            sort_on = self.getSort_on()
        if b_size == 0 and not batch_size and not batch:
            b_size = self.getLimit()
        if b_size == 0 and batch_size and batch:
            b_size = batch_size
        return self.getQuery(batch=batch, b_start=b_start, b_size=b_size, sort_on=sort_on, brains=brains, custom_query=custom_query)

    # for BBB with ATTopic
    security.declareProtected(View, 'queryCatalog')
    def queryCatalog(self, batch=True, b_start=0, b_size=30, sort_on=None, **kwargs):
        return self.results(batch, b_start, b_size, sort_on=sort_on, brains=True, custom_query=kwargs)

    # for BBB with ATTopic
    # This is used in Plone 4.2 but no longer in Plone 4.3
    security.declareProtected(View, 'synContentValues')
    def synContentValues(self):
        syn_tool = getToolByName(self, 'portal_syndication')
        limit = int(syn_tool.getMaxItems(self))
        return self.queryCatalog(batch=False, b_size=limit)[:limit]

    security.declareProtected(View, 'selectedViewFields')
    def selectedViewFields(self):
        """Get which metadata field are selected"""
        _mapping = {}
        for field in self.listMetaDataFields().items():
            _mapping[field[0]] = field
        return [_mapping[field] for field in self.customViewFields]

    security.declareProtected(View, 'getFoldersAndImages')
    def getFoldersAndImages(self):
        """Get folders and images"""
        catalog = getToolByName(self, 'portal_catalog')
        results = self.results(batch=False)

        _mapping = {'results': results, 'images': {}, 'others': []}
        portal_atct = getToolByName(self, 'portal_atct')
        image_types = getattr(portal_atct, 'image_types', [])

        for item in results:
            item_path = item.getPath()
            if item.isPrincipiaFolderish:
                query = {
                    'portal_type': image_types,
                    'path': item_path,
                }
                _mapping['images'][item_path] = IContentListing(catalog(query))
            elif item.portal_type in image_types:
                _mapping['images'][item_path] = [item, ]
            else:
                _mapping['others'].append(item._brain)

        _mapping['total_number_of_images'] = sum(map(len,
                                                _mapping['images'].values()))
        return _mapping


atapi.registerType(Collection, PROJECTNAME)
