import new
from Acquisition import aq_inner
from zope import interface
from zope.formlib import namedtemplate
from Products.Five.browser.pagetemplatefile import BoundPageTemplate
try:
    # chameleon-compatible page templates
    from five.pt.pagetemplate import ViewPageTemplateFile as ChameleonPageTemplateFile
    HAS_CHAMELEON = True
except ImportError:
    HAS_CHAMELEON = False

class NamedTemplateAdapter(object):
    """A named template adapter implementation that has the ability
    to lookup the template portion from regular traversal (intended for
    being able to customize the template portion of a view component
    in the traditional portal_skins style).
    """

    interface.implements(namedtemplate.INamedTemplate)

    def __init__(self, context):
        self.context = context

    @property
    def macros (self):
        return self.default_template.macros

    def __call__(self, *args, **kwargs):
        context = aq_inner(self.context)
        context_of_context = aq_inner(context.context)
        view = context.__of__(context_of_context)
        
        # self.default_template is a ViewPageTemplateFile, which is a property descriptor
        # whose __get__ method returns a BoundPageTemplate.  That expects to be accessed from
        # a view, but we're accessing it from a NamedTemplateAdapter so we have to be sneaky and
        # make our own BoundPageTemplate rather than calling self.default_template directly.
        return BoundPageTemplate(self.__class__.__dict__['default_template'], view)(*args, **kwargs)

def named_template_adapter(template):
    """Return a new named template adapter which defaults the to given
    template.
    """

    new_class = new.classobj('GeneratedClass', 
                             (NamedTemplateAdapter,),
                             {})
    if HAS_CHAMELEON:
        template = ChameleonPageTemplateFile(template.filename)
    new_class.default_template = template
    return new_class
