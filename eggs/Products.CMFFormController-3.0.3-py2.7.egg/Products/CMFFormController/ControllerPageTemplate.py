import os
from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from App.Common import package_home
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate as BaseClass
from Products.CMFCore.permissions import View
from BaseControllerPageTemplate import BaseControllerPageTemplate
from FormAction import FormActionContainer
from FormValidator import FormValidatorContainer

from urllib import quote

# ###########################################################################
# Product registration and Add support
manage_addControllerPageTemplateForm = PageTemplateFile('www/cptAdd', globals())
manage_addControllerPageTemplateForm.__name__='manage_addControllerPageTemplateForm'


def manage_addControllerPageTemplate(self, id, title=None, text=None,
                                    REQUEST=None, submit=None):
    """Add a Controller Page Template with optional file content."""

    id = str(id)
    if REQUEST is None:
        self._setObject(id, ControllerPageTemplate(id, text))
        ob = getattr(self, id)
        if title:
            ob.pt_setTitle(title)
        return ob
    else:
        file = REQUEST.form.get('file')
        headers = getattr(file, 'headers', None)
        if headers is None or not file.filename:
            zpt = ControllerPageTemplate(id)
        else:
            zpt = ControllerPageTemplate(id, file, headers.get('content_type'))

        self._setObject(id, zpt)

        try:
            u = self.DestinationURL()
        except AttributeError:
            u = REQUEST['URL1']

        if submit == " Add and Edit ":
            u = "%s/%s" % (u, quote(id))
        REQUEST.RESPONSE.redirect(u+'/manage_main')
    return ''

# ###########################################################################
class ControllerPageTemplate(BaseClass, BaseControllerPageTemplate):

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    manage_options = (BaseClass.manage_options[:2] + \
        ({'label':'Validation',
          'action':'manage_formValidatorsForm'},
         {'label':'Actions',
          'action':'manage_formActionsForm'},) +
        BaseClass.manage_options[2:])

    meta_type = 'Controller Page Template'

    _default_content_fn = os.path.join(package_home(globals()),
                                       'www', 'default.html')

    def __init__(self, *args, **kwargs):
        self.validators = FormValidatorContainer()
        self.actions = FormActionContainer()
        return ControllerPageTemplate.inheritedAttribute('__init__')(self, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        return self._call(ControllerPageTemplate.inheritedAttribute('__call__'), *args, **kwargs)

    def _notifyOfCopyTo(self, container, op=0):
        # BaseClass.inheritedAttribute('notifyOfCopyTo')(self, container, op)
        self._base_notifyOfCopyTo(container, op)

    def manage_afterAdd(self, object, container):
        BaseClass.inheritedAttribute('manage_afterAdd')(self, object, container)
        self._base_manage_afterAdd(object, container)

    def manage_afterClone(self, object):
        BaseClass.inheritedAttribute('manage_afterClone')(self, object)
        self._base_manage_afterClone(object)


InitializeClass(ControllerPageTemplate)
