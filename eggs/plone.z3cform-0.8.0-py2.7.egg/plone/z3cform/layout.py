from Acquisition import aq_inner
import z3c.form.interfaces

import zope.interface
import zope.component

from Products.Five import BrowserView

from zope.pagetemplate.interfaces import IPageTemplate

from Products.Five.browser.pagetemplatefile import BoundPageTemplate

from plone.z3cform import interfaces
from plone.z3cform import z2


class FormWrapper(BrowserView):
    """Use this as a base class for your Five view and override the
    'form' attribute with your z3c.form form class.  Your form will
    then be rendered in the contents area of a layout template, the
    'index' attribute.

    Use the 'wrap' function in this module if you don't like defining
    classes.
    """
    zope.interface.implements(interfaces.IFormWrapper)

    form = None # override this with a form class.
    index = None # override with a page template, or rely on an adapter
    request_layer = z3c.form.interfaces.IFormLayer

    def __init__(self, context, request):
        super(FormWrapper, self).__init__(context, request)
        if self.form is not None:
            self.form_instance = self.form(
                aq_inner(self.context), self.request)
            self.form_instance.__name__ = self.__name__

    def update(self):
        """On update, we switch on the zope3 request, needed to work with
        our z3c form. We update here the wrapped form.

        Override this method if you have more than one form.
        """

        if not z3c.form.interfaces.ISubForm.providedBy(self.form_instance):
            zope.interface.alsoProvides(self.form_instance, interfaces.IWrappedForm)

        z2.switch_on(self, request_layer=self.request_layer)
        self.form_instance.update()

        # If a form action redirected, don't render the wrapped form
        if self.request.response.getStatus() in (302, 303):
            self.contents = ""
            return

        # A z3c.form.form.AddForm does a redirect in its render method.
        # So we have to render the form to see if we have a redirection.
        # In the case of redirection, we don't render the layout at all.
        self.contents = self.form_instance.render()

    def __call__(self):
        """We use the update/render pattern. If a redirect happens in the
        meantime, we simply skip the rendering.
        """
        self.update()
        return self.render()

    def render(self):
        """This method renders the outer skeleton template, which in
        turn calls the 'contents' method below.

        We use an indirection to 'self.index' here to allow users to
        override the skeleton template through the 'browser' zcml
        directive. If no index template is set, we look up a an adapter from
        (self, request) to IPageTemplate and use that instead.
        """
        if self.request.response.getStatus() in (302, 303):
            return u""
        if self.index is None:
            template = zope.component.getMultiAdapter(
                (self, self.request), IPageTemplate)
            return BoundPageTemplate(template, self)()
        return self.index()

    def label(self):
        """Override this method to use a different way of acquiring a
        label or title for your page.  Overriding this with a simple
        attribute works as well.
        """
        return self.form_instance.label


def wrap_form(form, __wrapper_class=FormWrapper, **kwargs):
    class MyFormWrapper(__wrapper_class):
        pass
    assert z3c.form.interfaces.IForm.implementedBy(form)
    MyFormWrapper.form = form
    for name, value in kwargs.items():
        setattr(MyFormWrapper, name, value)
    return MyFormWrapper
