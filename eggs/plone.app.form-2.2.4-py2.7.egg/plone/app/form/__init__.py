from Products.Five.browser import pagetemplatefile
from plone.app.form._named import named_template_adapter
from zope.formlib import namedtemplate, interfaces
from zope import i18n

from plone.app.form import _patches
_patches.apply_patches()

@namedtemplate.implementation(interfaces.IAction)
def render_submit_button(self):
    """A custom version of the submit button that uses plone's context class"""
    if not self.available():
        return ''
    label = self.label
    if isinstance(label, i18n.Message):
        label = i18n.translate(self.label, context=self.form.request)
    return ('<input type="submit" id="%s" name="%s" value="%s"'
            ' class="context" />' %
            (self.__name__, self.__name__, label)
            )

__all__ = ('named_template_adapter', 'default_named_template')

_template = pagetemplatefile.ViewPageTemplateFile('pageform.pt')
default_named_template_adapter = named_template_adapter(_template)

_subpage_template = pagetemplatefile.ViewPageTemplateFile('subpageform.pt')
default_subpage_template = named_template_adapter(_subpage_template)

_template = pagetemplatefile.ViewPageTemplateFile('addingpageform.pt')
adding_named_template_adapter = named_template_adapter(_template)

from zope.i18nmessageid import MessageFactory
PloneMessageFactory = MessageFactory('plone')
