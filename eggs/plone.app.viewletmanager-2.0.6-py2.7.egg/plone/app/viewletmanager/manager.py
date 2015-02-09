from zope.interface import implements
from zope.component import getUtility, getAdapters, queryUtility
from zope.component import getMultiAdapter, queryMultiAdapter

from zope.viewlet.interfaces import IViewlet
from zope.contentprovider.interfaces import IContentProvider

from zope.interface import providedBy

from Acquisition import aq_base
from Acquisition.interfaces import IAcquirer
from AccessControl.ZopeGuards import guarded_hasattr
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from plone.app.viewletmanager.interfaces import IViewletSettingsStorage
from plone.app.viewletmanager.interfaces import IViewletManagementView

from cgi import parse_qs
from logging import getLogger
import traceback
from urllib import urlencode
from ZODB.POSException import ConflictError

logger = getLogger('plone.app.viewletmanager')


class BaseOrderedViewletManager(object):

    _uncatched_errors = (ConflictError, KeyboardInterrupt)

    def filter(self, viewlets):
        """Filter the viewlets.

        ``viewlets`` is a list of tuples of the form (name, viewlet).

        This filters the viewlets just like Five, but also filters out
        viewlets by name from the local utility which implements the
        IViewletSettingsStorage interface.
        """
        results = []
        storage = queryUtility(IViewletSettingsStorage)
        if storage is None:
            return results
        skinname = self.context.getCurrentSkinName()
        hidden = frozenset(storage.getHidden(self.__name__, skinname))
        # Only return visible viewlets accessible to the principal
        # We need to wrap each viewlet in its context to make sure that
        # the object has a real context from which to determine owner
        # security.
        # Copied from Five
        for name, viewlet in viewlets:
            if IAcquirer.providedBy(viewlet):
                viewlet = viewlet.__of__(viewlet.context)
            if name not in hidden and guarded_hasattr(viewlet, 'render'):
                results.append((name, viewlet))
        return results

    def sort(self, viewlets):
        """Sort the viewlets.

        ``viewlets`` is a list of tuples of the form (name, viewlet).

        This sorts the viewlets by the order looked up from the local utility
        which implements the IViewletSettingsStorage interface. The remaining
        ones are sorted just like Five does it.
        """
        result = []
        storage = queryUtility(IViewletSettingsStorage)
        if storage is None:
            return result
        skinname = self.context.getCurrentSkinName()
        order_by_name = storage.getOrder(self.__name__, skinname)
        # first get the known ones
        name_map = dict(viewlets)
        for name in order_by_name:
            if name in name_map:
                result.append((name, name_map[name]))
                del name_map[name]

        # then sort the remaining ones
        # Copied from Five
        remaining = sorted(name_map.items(),
                           lambda x, y: cmp(aq_base(x[1]), aq_base(y[1])))

        # return both together
        return result + remaining

    def render(self):
        if self.template:
            try:
                return self.template(viewlets=self.viewlets)
            except self._uncatched_errors:
                raise
            except Exception, e:
                trace = traceback.format_exc()
                name = self.__name__
                msg = "rendering of %s fails: %s\n%s\n"
                logger.error(msg % (name, e, trace))
                return u"error while rendering %s\n" % name
        else:
            html = []
            for viewlet in self.viewlets:
                try:
                    html.append(viewlet.render())
                except self._uncatched_errors:
                    raise
                except Exception, e:
                    name = self.__name__
                    trace = traceback.format_exc()
                    vname = viewlet.__name__
                    msg = "rendering of %s in %s fails: %s\n%s\n"
                    logger.error(msg % (name, vname, e, trace))
                    html.append(u"error while rendering %s\n" % vname)
            return u"\n".join(html)


class OrderedViewletManager(BaseOrderedViewletManager):
    manager_template = ViewPageTemplateFile('manage-viewletmanager.pt')

    def render(self):
        """See zope.contentprovider.interfaces.IContentProvider"""

        # check whether we are in the manager view
        is_managing = False
        parent = getattr(self, '__parent__', None)
        while parent is not None:
            if IViewletManagementView.providedBy(parent):
                is_managing = True
                break
            parent = getattr(parent, '__parent__', None)

        if is_managing:
            # if we are in the managing view, then fetch all viewlets again
            viewlets = getAdapters(
                (self.context, self.request, self.__parent__, self),
                IViewlet)

            # sort them first
            viewlets = self.sort(viewlets)

            storage = getUtility(IViewletSettingsStorage)
            skinname = self.context.getCurrentSkinName()
            hidden = frozenset(storage.getHidden(self.__name__, skinname))

            # then render the ones which are accessible
            base_url = str(getMultiAdapter((self.context, self.request),
                           name='absolute_url'))
            query_tmpl = "%s/@@manage-viewlets?%%s" % base_url
            results = []
            for index, (name, viewlet) in enumerate(viewlets):
                if IAcquirer.providedBy(viewlet):
                    viewlet = viewlet.__of__(viewlet.context)
                viewlet_id = "%s:%s" % (self.__name__, name)
                options = {'index': index,
                           'name': name,
                           'hidden': name in hidden,
                           'show_url': query_tmpl % urlencode({'show': viewlet_id}),
                           'hide_url': query_tmpl % urlencode({'hide': viewlet_id})}

                if guarded_hasattr(viewlet, 'render'):
                    viewlet.update()
                    options['content'] = viewlet.render()
                else:
                    options['content'] = u""
                if index > 0:
                    prev_viewlet = viewlets[index-1][0]
                    query = {'move_above': "%s;%s" % (viewlet_id, prev_viewlet)}
                    options['up_url'] = query_tmpl % urlencode(query)
                if index < (len(viewlets) - 1):
                    next_viewlet = viewlets[index+1][0]
                    query = {'move_below': "%s;%s" % (viewlet_id, next_viewlet)}
                    options['down_url'] = query_tmpl % urlencode(query)
                results.append(options)

            self.name = self.__name__
            self.normalized_name = self.name.replace('.', '-')
            self.interface = list(providedBy(self).flattened())[0].__identifier__

            # and output them
            return self.manager_template(viewlets=results)
        # the rest is standard behaviour from zope.viewlet
        else:
            return BaseOrderedViewletManager.render(self)


class ManageViewlets(BrowserView):
    implements(IViewletManagementView)

    def show(self, manager, viewlet):
        storage = getUtility(IViewletSettingsStorage)
        skinname = self.context.getCurrentSkinName()
        hidden = storage.getHidden(manager, skinname)
        if viewlet in hidden:
            hidden = tuple(x for x in hidden if x != viewlet)
            storage.setHidden(manager, skinname, hidden)

    def hide(self, manager, viewlet):
        storage = getUtility(IViewletSettingsStorage)
        skinname = self.context.getCurrentSkinName()
        hidden = storage.getHidden(manager, skinname)
        if viewlet not in hidden:
            hidden = hidden + (viewlet, )
            storage.setHidden(manager, skinname, hidden)

    def _getOrder(self, manager_name):
        storage = getUtility(IViewletSettingsStorage)
        skinname = self.context.getCurrentSkinName()
        manager = queryMultiAdapter(
            (self.context, self.request, self), IContentProvider, manager_name)
        viewlets = getAdapters(
            (manager.context, manager.request, manager.__parent__, manager),
            IViewlet)
        order_by_name = storage.getOrder(manager_name, skinname)
        # first get the known ones
        name_map = dict(viewlets)
        result = []
        for name in order_by_name:
            if name in name_map:
                result.append((name, name_map[name]))
                del name_map[name]

        # then sort the remaining ones
        # Copied from Five
        remaining = sorted(name_map.items(),
                           lambda x, y: cmp(aq_base(x[1]), aq_base(y[1])))

        return [x[0] for x in result + remaining]

    def moveAbove(self, manager, viewlet, dest):
        storage = getUtility(IViewletSettingsStorage)
        skinname = self.context.getCurrentSkinName()
        order = self._getOrder(manager)
        viewlet_index = order.index(viewlet)
        del order[viewlet_index]
        dest_index = order.index(dest)
        order.insert(dest_index, viewlet)
        storage.setOrder(manager, skinname, order)

    def moveBelow(self, manager, viewlet, dest):
        storage = getUtility(IViewletSettingsStorage)
        skinname = self.context.getCurrentSkinName()
        order = self._getOrder(manager)
        viewlet_index = order.index(viewlet)
        del order[viewlet_index]
        dest_index = order.index(dest)
        order.insert(dest_index+1, viewlet)
        storage.setOrder(manager, skinname, order)

    def __call__(self):
        base_url = "%s/@@manage-viewlets" % str(
                       getMultiAdapter((self.context, self.request),
                       name='absolute_url'))
        qs = self.request.get('QUERY_STRING', None)
        if qs is not None:
            query = parse_qs(qs)
            if 'show' in query:
                for name in query['show']:
                    manager, viewlet = name.split(':')
                    self.show(manager, viewlet)
                    self.request.response.redirect(base_url)
                    return ''
            if 'hide' in query:
                for name in query['hide']:
                    manager, viewlet = name.split(':')
                    self.hide(manager, viewlet)
                    self.request.response.redirect(base_url)
                    return ''
            if 'move_above' in query:
                for name in query['move_above']:
                    manager, viewlets = name.split(':')
                    viewlet, dest = viewlets.split(';')
                    self.moveAbove(manager, viewlet, dest)
                    self.request.response.redirect(base_url)
                    return ''
            if 'move_below' in query:
                for name in query['move_below']:
                    manager, viewlets = name.split(':')
                    viewlet, dest = viewlets.split(';')
                    self.moveBelow(manager, viewlet, dest)
                    self.request.response.redirect(base_url)
                    return ''
        return self.index()
