"""This module provides "form template factories" that can be
registered to provide default form templates for forms and subforms.

The default templates draw from a macro page template which you can use by
itself to render parts of it.
"""

from Acquisition import IAcquirer, ImplicitAcquisitionWrapper

import os
import zope.publisher.browser

import z3c.form.interfaces
import z3c.form.form
import z3c.form.widget

from z3c.form import util
from zope.pagetemplate.interfaces import IPageTemplate

try:
    # chameleon-compatible page templates
    from five.pt.pagetemplate import ViewPageTemplateFile
    from five.pt.pagetemplate import ViewPageTemplateFile as ZopeTwoPageTemplateFile
except ImportError:
    # standard Zope page templates
    from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile as ZopeTwoPageTemplateFile
    from zope.browserpage.viewpagetemplatefile import ViewPageTemplateFile

import plone.z3cform
import plone.z3cform.layout

path = lambda p: os.path.join(os.path.dirname(plone.z3cform.__file__), 'templates', p)

# Zope 2-compatible form and widget template factory classes.

class FormTemplateFactory(z3c.form.form.FormTemplateFactory):
    """Form template factory that will use Chameleon if installed (via
    five.pt), or the Zope 2 ViewPageTemplateFile from Products.Five if not.

    You can use this for a wrapped form, but not for a form that is going
    to be rendered as a standalone view. Use ZopeTwoFormTemplateFactory for
    that instead.
    """

    def __init__(self, filename, contentType='text/html', form=None, request=None):
        self.template = ViewPageTemplateFile(filename, content_type=contentType)
        zope.component.adapter(
            util.getSpecification(form),
            util.getSpecification(request))(self)
        zope.interface.implementer(IPageTemplate)(self)

class ZopeTwoFormTemplateFactory(z3c.form.form.FormTemplateFactory):
    """Form template factory for Zope 2 page templates.

    Use this for any form which is going to be rendered as a view, or any
    form wrapper view.
    """

    def __init__(self, filename, contentType='text/html', form=None, request=None):
        self.template = ZopeTwoPageTemplateFile(filename, content_type=contentType)
        zope.component.adapter(
            util.getSpecification(form),
            util.getSpecification(request))(self)
        zope.interface.implementer(IPageTemplate)(self)

    def __call__(self, form, request):
        template = self.template
        if IAcquirer.providedBy(template):
            return ImplicitAcquisitionWrapper(template, form)
        else:
            return template

class ZopeTwoWidgetTemplateFactory(z3c.form.widget.WidgetTemplateFactory):
    """A variant of z3c.form's widget.WidgetTemplateFactory which uses Zope 2
    page templates. This should only be necessary if you strictly need the
    extra Zope 2-isms of Five's ViewPageTemplateFile.
    """

    def __init__(self, filename, contentType='text/html', context=None,
        request=None, view=None, field=None, widget=None
    ):
        self.template = ViewPageTemplateFile(filename, content_type=contentType)
        zope.component.adapter(
            util.getSpecification(context),
            util.getSpecification(request),
            util.getSpecification(view),
            util.getSpecification(field),
            util.getSpecification(widget))(self)
        zope.interface.implementer(IPageTemplate)(self)

# View containing common macros

class Macros(zope.publisher.browser.BrowserView):

    def __getitem__(self, key):
        return self.index.macros[key]

# Default templates for the wrapped layout view use case

layout_factory = ZopeTwoFormTemplateFactory(path('layout.pt'),
        form=plone.z3cform.interfaces.IFormWrapper
    )

wrapped_form_factory = FormTemplateFactory(path('wrappedform.pt'),
        form=plone.z3cform.interfaces.IWrappedForm,
    )

# Default templates for the standalone form use case

standalone_form_factory = ZopeTwoFormTemplateFactory(path('form.pt'),
        form=z3c.form.interfaces.IForm
    )

# Default templates for subforms

subform_factory = FormTemplateFactory(path('subform.pt'),
        form=z3c.form.interfaces.ISubForm
    )
