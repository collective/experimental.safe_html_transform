from AccessControl import ClassSecurityInfo
from App.class_init import InitializeClass
from Products.CMFCore.permissions import View
from Products.CMFCore.utils import getToolByName
from ControllerBase import ControllerBase

class BaseControllerPageTemplate(ControllerBase):

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    def _call(self, inherited_call, *args, **kwargs):
        # Intercept a call to a form and see if REQUEST.form contains the
        # value form.submitted.  If so, perform validation.  If not, update
        # the controller state and treat as a normal form.

        REQUEST = self.REQUEST

        controller = getToolByName(self, 'portal_form_controller')
        controller_state = controller.getState(self, is_validator=0)

        form_submitted = REQUEST.form.get('form.submitted', None)
        if form_submitted:
            controller_state = self.getButton(controller_state, REQUEST)
            validators = self.getValidators(controller_state, REQUEST).getValidators()
            controller_state = controller.validate(controller_state, REQUEST, validators)
            del REQUEST.form['form.submitted']
            return self.getNext(controller_state, REQUEST)

        kwargs['state'] = controller_state
        return inherited_call(self, *args, **kwargs)


InitializeClass(BaseControllerPageTemplate)
