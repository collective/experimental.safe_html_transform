import random

from AccessControl import getSecurityManager

from zope.interface import implements
from zope.component import getMultiAdapter, getUtility

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from zope import schema
from zope.formlib import form

from plone.memoize.instance import memoize

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.vocabularies.catalog import SearchableTextSourceBinder
from plone.app.form.widgets.uberselectionwidget import UberSelectionWidget

from plone.i18n.normalizer.interfaces import IIDNormalizer

from plone.portlet.collection import PloneMessageFactory as _


class ICollectionPortlet(IPortletDataProvider):
    """A portlet which renders the results of a collection object.
    """

    header = schema.TextLine(
        title=_(u"Portlet header"),
        description=_(u"Title of the rendered portlet"),
        required=True)

    target_collection = schema.Choice(
        title=_(u"Target collection"),
        description=_(u"Find the collection which provides the items to list"),
        required=True,
        source=SearchableTextSourceBinder(
            {'portal_type': ('Topic', 'Collection')},
            default_query='path:'))

    limit = schema.Int(
        title=_(u"Limit"),
        description=_(u"Specify the maximum number of items to show in the "
                      u"portlet. Leave this blank to show all items."),
        required=False)

    random = schema.Bool(
        title=_(u"Select random items"),
        description=_(u"If enabled, items will be selected randomly from the "
                      u"collection, rather than based on its sort order."),
        required=True,
        default=False)

    show_more = schema.Bool(
        title=_(u"Show more... link"),
        description=_(u"If enabled, a more... link will appear in the footer "
                      u"of the portlet, linking to the underlying "
                      u"Collection."),
        required=True,
        default=True)

    show_dates = schema.Bool(
        title=_(u"Show dates"),
        description=_(u"If enabled, effective dates will be shown underneath "
                      u"the items listed."),
        required=True,
        default=False)

    exclude_context = schema.Bool(
        title=_(u"Exclude the Current Context"),
        description=_(
            u"If enabled, the listing will not include the current item the "
            u"portlet is rendered for if it otherwise would be."),
        required=True,
        default=True)


class Assignment(base.Assignment):
    """
    Portlet assignment.
    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    implements(ICollectionPortlet)

    header = u""
    target_collection = None
    limit = None
    random = False
    show_more = True
    show_dates = False

    def __init__(self, header=u"", target_collection=None, limit=None,
                 random=False, show_more=True, show_dates=False,
                 exclude_context=True):
        self.header = header
        self.target_collection = target_collection
        self.limit = limit
        self.random = random
        self.show_more = show_more
        self.show_dates = show_dates
        self.exclude_context = exclude_context

    @property
    def title(self):
        """This property is used to give the title of the portlet in the
        "manage portlets" screen. Here, we use the title that the user gave.
        """
        return self.header


class Renderer(base.Renderer):

    _template = ViewPageTemplateFile('collection.pt')
    render = _template

    def __init__(self, *args):
        base.Renderer.__init__(self, *args)

    @property
    def available(self):
        return len(self.results())

    def collection_url(self):
        collection = self.collection()
        if collection is None:
            return None
        else:
            return collection.absolute_url()

    def css_class(self):
        header = self.data.header
        normalizer = getUtility(IIDNormalizer)
        return "portlet-collection-%s" % normalizer.normalize(header)

    @memoize
    def results(self):
        if self.data.random:
            return self._random_results()
        else:
            return self._standard_results()

    def _standard_results(self):
        results = []
        collection = self.collection()
        if collection is not None:
            context_path = '/'.join(self.context.getPhysicalPath())
            exclude_context = getattr(self.data, 'exclude_context', False)
            limit = self.data.limit
            if limit and limit > 0:
                # pass on batching hints to the catalog
                results = collection.queryCatalog(
                    batch=True, b_size=limit  + exclude_context)
                results = results._sequence
            else:
                results = collection.queryCatalog()
            if exclude_context:
                results = [
                    brain for brain in results
                    if brain.getPath() != context_path]
            if limit and limit > 0:
                results = results[:limit]
        return results

    def _random_results(self):
        # intentionally non-memoized
        results = []
        collection = self.collection()
        if collection is not None:
            context_path = '/'.join(self.context.getPhysicalPath())
            exclude_context = getattr(self.data, 'exclude_context', False)
            results = collection.queryCatalog(sort_on=None)
            if results is None:
                return []
            limit = self.data.limit and min(len(results), self.data.limit) or 1

            if exclude_context:
                results = [
                    brain for brain in results
                    if brain.getPath() != context_path]
            if len(results) < limit:
                limit = len(results)
            results = random.sample(results, limit)

        return results

    @memoize
    def collection(self):
        collection_path = self.data.target_collection
        if not collection_path:
            return None

        if collection_path.startswith('/'):
            collection_path = collection_path[1:]

        if not collection_path:
            return None

        portal_state = getMultiAdapter((self.context, self.request),
                                       name=u'plone_portal_state')
        portal = portal_state.portal()
        if isinstance(collection_path, unicode):
            # restrictedTraverse accepts only strings
            collection_path = str(collection_path)

        result = portal.unrestrictedTraverse(collection_path, default=None)
        if result is not None:
            sm = getSecurityManager()
            if not sm.checkPermission('View', result):
                result = None
        return result
        
    def include_empty_footer(self):
        """
        Whether or not to include an empty footer element when the more 
        link is turned off.
        Always returns True (this method provides a hook for 
        sub-classes to override the default behaviour).
        """
        return True


class AddForm(base.AddForm):

    form_fields = form.Fields(ICollectionPortlet)
    form_fields['target_collection'].custom_widget = UberSelectionWidget

    label = _(u"Add Collection Portlet")
    description = _(u"This portlet displays a listing of items from a "
                    u"Collection.")

    def create(self, data):
        return Assignment(**data)


class EditForm(base.EditForm):

    form_fields = form.Fields(ICollectionPortlet)
    form_fields['target_collection'].custom_widget = UberSelectionWidget

    label = _(u"Edit Collection Portlet")
    description = _(u"This portlet displays a listing of items from a "
                    u"Collection.")
