from zope.component import adapter, getSiteManager
from zope.viewlet.viewlet import ViewletBase
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from zope.lifecycleevent.interfaces import IObjectRemovedEvent
from zope.viewlet.interfaces import IViewlet, IViewletManager
from zope.interface import implements

from five.customerize.interfaces import ITTWViewTemplate
from five.customerize.utils import checkPermission
from plone.portlets.interfaces import IPortletRenderer
from plone.portlets.interfaces import IPortletManager


class TTWViewTemplate(ZopePageTemplate):
    """A template class used to generate Zope 3 views TTW"""
    implements(ITTWViewTemplate)

    manage_options = (
        ZopePageTemplate.manage_options[0],
        dict(label='Registrations', action='registrations.html'),
        ) + ZopePageTemplate.manage_options[2:]

    def __init__(self, id, text=None, content_type='text/html', strict=True,
                 encoding='utf-8', view=None, permission=None, name=None):
        self.view = view
        self.permission = permission
        self.name = name
        super(TTWViewTemplate, self).__init__(id, text, content_type, encoding,
                                              strict)

    def __call__(self, context, request, view=None, manager=None, data=None):
        #XXX raise a sensible exception if context and request are
        # omitted, IOW, if someone tries to render the template not as
        # a view.

        # the security check is now deferred until the template/viewlet/portlet
        # is actually called, because it may be looked up during traversal,
        # in which case there's no proper security context yet
        if IPortletManager.providedBy(manager):
            return TTWPortletRenderer(context, request, self, view,
                manager, data, self.permission)
        if IViewletManager.providedBy(manager):
            return TTWViewletRenderer(context, request, self, view,
                manager, self.permission)
        else:
            return TTWViewTemplateRenderer(context, request, self, self.permission)

    # overwrite Shared.DC.Scripts.Binding.Binding's before traversal
    # hook that would prevent to look up views for instances of this
    # class.
    def __before_publishing_traverse__(self, self2, request):
        pass


class TTWViewTemplateRenderer(object):
    """The view object for the TTW View Template.

    When a TTWViewTemplate-based view is looked up, an object of this
    class is instantiated.  It holds a reference to the
    TTWViewTemplate object which it will use in the render process
    (__call__).
    """

    def __init__(self, context, request, template, permission=None):
        self.context = context
        self.request = request
        self.template = template
        self.view = None
        self.permission = permission

    def __call__(self, *args, **kwargs):
        """Render the TTWViewTemplate-based view.
        """
        view = self._getView()
        # we need to override the template's context and request as
        # they generally point to the wrong objects (a template's
        # context usually is what it was acquired from, which isn't
        # what the context is for a view template).
        bound_names = {'context': self.context,
                       'request': self.request,
                       'view': view}
        template = self.template.__of__(self.context)
        return template._exec(bound_names, args, kwargs)

    def _getView(self):
        checkPermission(self.permission, self.context)
        if self.view is not None:
            return self.view
        view_class = self.template.view
        if view_class is not None:
            # Filesystem-based view templates are trusted code and
            # have unrestricted access to the view class.  We simulate
            # that for TTW templates (which are trusted code) by
            # creating a subclass with unrestricted access to all
            # subobjects.
            if hasattr(view_class, '_five_customerize_ttw_class'):
                TTWView = view_class._five_customerize_ttw_class
            else:
                class TTWView(view_class):
                    __allow_access_to_unprotected_subobjects__ = 1
                view_class._five_customerize_ttw_class = TTWView
            self.view = TTWView(self.context, self.request)
            return self.view

    # Zope 2 wants to acquisition-wrap every view object (via __of__).
    # We don't need this as the TTWViewTemplate object is already
    # properly acquisition-wrapped in __call__.  Nevertheless we need
    # to support the __of__ method as a no-op.
    def __of__(self, obj):
        return self

    # Make sure this object passes the ZPublisher's security validation
    @property
    def __parent__(self):
        return self.context


class TTWViewletRenderer(object):
    """ analogon to TTWViewTemplateRenderer for viewlets """
    implements(IViewlet)

    __allow_access_to_unprotected_subobjects__ = True

    def __init__(self, context, request, template, view, manager=None, permission=None):
        self.context = context
        self.request = request
        self.template = template
        self.view = view
        self.manager = manager
        self.viewlet = None
        self.permission = permission

    def update(self):
        """ update the viewlet before `render` is called """
        self._getViewlet().update()

    def render(self, *args, **kwargs):
        """ render the viewlet using the customized template """
        viewlet = self._getViewlet()
        # we need to override the template's context and request as
        # they generally point to the wrong objects (a template's
        # context usually is what it was acquired from, which isn't
        # what the context is for a view template).
        bound_names = {'context': self.context,
                       'request': self.request,
                       'view': viewlet}
        template = self.template.__of__(self.context)
        return template._exec(bound_names, args, kwargs)

    def _getViewlet(self):
        checkPermission(self.permission, self.context)
        if self.viewlet is not None:
            return self.viewlet
        view_class = self.template.view
        if view_class is not None:
            # Filesystem-based view templates are trusted code and
            # have unrestricted access to the view class.  We simulate
            # that for TTW templates (which are trusted code) by
            # creating a subclass with unrestricted access to all
            # subobjects.
            if hasattr(view_class, '_five_customerize_ttw_class'):
                TTWViewlet = view_class._five_customerize_ttw_class
            else:
                class TTWViewlet(view_class, ViewletBase):
                    __allow_access_to_unprotected_subobjects__ = 1
                view_class._five_customerize_ttw_class = TTWViewlet
            self.viewlet = TTWViewlet(self.context, self.request, self.view, self.manager)
            return self.viewlet

    # Zope 2 wants to acquisition-wrap every view object (via __of__).
    # We don't need this as the TTWViewTemplate object is already
    # properly acquisition-wrapped in __call__.  Nevertheless we need
    # to support the __of__ method as a no-op.
    def __of__(self, obj):
        return self


class TTWPortletRenderer(object):
    """ analogon to TTWViewletRenderer for portlets """
    implements(IPortletRenderer)

    __allow_access_to_unprotected_subobjects__ = True

    def __init__(self, context, request, template, view, manager=None, data=None, permission=None):
        self.context = context
        self.request = request
        self.template = template
        self.view = view
        self.manager = manager
        self.data = data
        self.renderer = None
        self.permission = permission

    def update(self):
        """ update the portlet before `render` is called """
        self._getRenderer().update()

    def render(self, *args, **kwargs):
        """ render the portlet using the customized template """
        renderer = self._getRenderer()
        # we need to override the template's context and request as
        # they generally point to the wrong objects (a template's
        # context usually is what it was acquired from, which isn't
        # what the context is for a view template).
        bound_names = {'context': self.context,
                       'request': self.request,
                       'view': renderer}
        template = self.template.__of__(self.context)
        return template._exec(bound_names, args, kwargs)

    def _getRenderer(self):
        checkPermission(self.permission, self.context)
        if self.renderer is not None:
            return self.renderer
        view_class = self.template.view
        if view_class is not None:
            # Filesystem-based view templates are trusted code and
            # have unrestricted access to the view class.  We simulate
            # that for TTW templates (which are trusted code) by
            # creating a subclass with unrestricted access to all
            # subobjects.
            if hasattr(view_class, '_five_customerize_ttw_class'):
                TTWPortlet = view_class._five_customerize_ttw_class
            else:
                class TTWPortlet(view_class):
                    __allow_access_to_unprotected_subobjects__ = 1
                view_class._five_customerize_ttw_class = TTWPortlet
            self.renderer = TTWPortlet(self.context, self.request, self.view, self.manager, self.data)
            return self.renderer

    @property
    def available(self):
        return self._getRenderer().available

    # Zope 2 wants to acquisition-wrap every view object (via __of__).
    # We don't need this as the TTWViewTemplate object is already
    # properly acquisition-wrapped in __call__.  Nevertheless we need
    # to support the __of__ method as a no-op.
    def __of__(self, obj):
        return self


@adapter(TTWViewTemplate, IObjectRemovedEvent)
def unregisterViewWhenZPTIsDeleted(zpt, event):
    components = getSiteManager(zpt)
    for reg in components.registeredAdapters():
        if reg.factory == zpt:
            components.unregisterAdapter(reg.factory, reg.required,
                                         reg.provided, reg.name)
            break

