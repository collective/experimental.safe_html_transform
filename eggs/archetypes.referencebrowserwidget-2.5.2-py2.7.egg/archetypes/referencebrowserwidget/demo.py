""" demonstrates the use of archetypes.referencebrowserwidget """

from Products.Archetypes.atapi import ReferenceField
from Products.Archetypes.atapi import BaseSchema
from Products.Archetypes.atapi import Schema
from Products.Archetypes.atapi import BaseContent
from Products.Archetypes.atapi import registerType
from DateTime import DateTime

from archetypes.referencebrowserwidget.config import PROJECTNAME
from archetypes.referencebrowserwidget.widget import ReferenceBrowserWidget

schema = BaseSchema.copy() + Schema((

    ReferenceField('singleRef',
        multiValued=0,
        allowed_types=('Document', 'File', 'RefBrowserDemo'),
        relationship='Rel1',
        widget=ReferenceBrowserWidget(
            default_search_index='SearchableText',
            description='This is the first field. Pick an object. Restricted to Document, File and RefBrowserDemo.')),

    ReferenceField('multiRef',
        multiValued=1,
        relationship='Rel2',
        referencesSortable=1,
        widget=ReferenceBrowserWidget(
            hide_inaccessible=1,
            show_indexes=1,
            allow_sorting=1,
            description=('And here is another field with a longer '
                         'description text to explain the user better what '
                         'to do with this field.  Sort order can be changed for this field. Moreover, "hide_inaccessible" '
                         'is activated so referenced elements are hidden for members that can not access them.'))),

    ReferenceField('multiRef2',
        multiValued=1,
        relationship='Rel3',
        widget=ReferenceBrowserWidget(
            allow_search=1,
            allow_browse=0,
            force_close_on_insert=1,
            show_indexes=1,
            available_indexes={'SearchableText': 'Free text search',
                               'Description': "Object's description"},
            description='And here is another field.  Available indexes are "SearchableText" and "Description"')),

    ReferenceField('multiRef3',
        multiValued=1,
        relationship='Rel3',
        widget=ReferenceBrowserWidget(
            show_indexes=1,
            history_length=5,
            description='And here is another field.  Startup directory is /Members.',
            startup_directory='/Members')),

    ReferenceField('multiRef4',
        multiValued=1,
        relationship='Rel4',
        widget=ReferenceBrowserWidget(
            show_indexes=1,
            allow_browse=0,
            description=('And here is another field with a fixed query '
                         'restriction (only published objects will appear).'),
            base_query={'review_state': 'published'})),

    ReferenceField('multiRef5',
        multiValued=1,
        relationship='Rel5',
        widget=ReferenceBrowserWidget(
            show_indexes=1,
            allow_browse=0,
            description=('And here is another field with some dynamic '
                         'query restrictions (only objects with "start" '
                         'withing one week of the current date will appear).'),
            base_query='dynamicBaseQuery',
            popup_width=173,
            popup_height=209))
     ))


class RefBrowserDemo(BaseContent):
    """
    Demo from archetypes.referencebrowserwidget
    """
    content_icon = "document_icon.gif"
    schema = schema

    def dynamicBaseQuery(self):
        """  This example function generates a base query which ensures that
             only objects whose start property is within one week of the
             current day
        """
        current_week = [DateTime()-7, DateTime()+7]
        return {'start': {'query': current_week, 'range': 'minmax'}}

    def dynamicDirectory(self):
        return '/bar/dynamic'

    constantDirectory = '/foo/constant'

registerType(RefBrowserDemo, PROJECTNAME)
