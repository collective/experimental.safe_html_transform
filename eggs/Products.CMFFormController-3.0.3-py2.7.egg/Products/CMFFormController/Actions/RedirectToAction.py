from BaseFormAction import BaseFormAction
import RedirectTo

from Products.CMFCore.utils import getToolByName
from Products.CMFFormController.FormController import registerFormAction

def factory(arg):
    """Create a new redirect-to-action action"""
    return RedirectToAction(arg)


class RedirectToAction(BaseFormAction):

    def __call__(self, controller_state):
        action = self.getArg(controller_state)
        action_url = None
        haveAction = False

        context = controller_state.getContext()
        fti = context.getTypeInfo()

        try:
            # Test to see if the action is defined in the FTI as an object or
            # folder action
            action_ob = fti.getActionObject('object/'+action)
            if action_ob is None:
                action_ob = fti.getActionObject('folder/'+action)
            action_url = action_ob.getActionExpression()
            haveAction = True
        except (ValueError, AttributeError):
            actions_tool = getToolByName(context, 'portal_actions')
            actions = actions_tool.listFilteredActionsFor(
                                                controller_state.getContext())
            # flatten the actions as we don't care where they are
            actions = reduce(lambda x,y,a=actions:  x+a[y], actions.keys(), [])
            for actiondict in actions:
                if actiondict['id'] == action:
                    action_url = actiondict['url'].strip()
                    haveAction = True
                    break

        # (note: action_url may now be an emptry string, but still valid)
        if not haveAction:
            raise ValueError, 'No %s action found for %s' % (action, controller_state.getContext().getId())

        # XXX: Is there a better way to check this?
        if not action_url.startswith('string:'):
            action_url = 'string:%s' % (action_url,)
        return RedirectTo.RedirectTo(action_url)(controller_state)

registerFormAction('redirect_to_action',
                   factory,
                   'Redirect to the action specified in the argument (a TALES expression) for the current context object (e.g. string:view)')
