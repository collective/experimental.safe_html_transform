from BaseFormAction import BaseFormAction
import TraverseTo

from Products.CMFCore.utils import getToolByName
from Products.CMFFormController.FormController import registerFormAction
from urlparse import urlsplit

def factory(arg):
    """Create a new traverse-to-action action"""
    return TraverseToAction(arg)


class TraverseToAction(BaseFormAction):

    def __call__(self, controller_state):
        action = self.getArg(controller_state)
        action_url = None
        haveAction = False

        context = controller_state.getContext()
        actions_tool = getToolByName(context, 'portal_actions')
        fti = context.getTypeInfo()
        REQUEST = getattr(context, 'REQUEST', None)

        try:
            # Test to see if the action is defined in the FTI as an object or
            # folder action
            action_ob = fti.getActionObject('object/'+action)
            if action_ob is None:
                action_ob = fti.getActionObject('folder/'+action)
            # Use portal actions here so we have a full expression context
            ec = actions_tool._getExprContext(context)
            actiondict = action_ob.getAction(ec)
            haveAction = True
        except (ValueError, AttributeError):
            actions = actions_tool.listFilteredActionsFor(
                                                controller_state.getContext())
            # flatten the actions as we don't care where they are
            actions = reduce(lambda x,y,a=actions:  x+a[y], actions.keys(), [])
            for actiondict in actions:
                if actiondict['id'] == action:
                    haveAction = True
                    break
        # For traversal, our 'url' must be a traversable path
        if haveAction:
            action_url = actiondict['url'].strip()
            url_parts = urlsplit(action_url)
            # Check to see if we have a protocol, if so convert to a path,
            # otherwise make the assumption that we are dealing with a
            # physical path
            if url_parts[0] and REQUEST is not None:
                action_url = '/'.join(REQUEST.physicalPathFromURL(action_url))
            else:
                action_url = url_parts[2]
        else:
            raise ValueError, 'No %s action found for %s' % (action, controller_state.getContext().getId())

        # If we have CMF 1.5, the actual action_url may be hidden behind a method
        # alias. Attempt to resolve this
        try:
            if action_url:
                # If our url is a path, then we need to see if it contains the
                # path to the current object, if so we need to check if the
                # remaining path element is a method alias
                possible_alias = action_url
                current_path = '/'.join(context.getPhysicalPath())
                if possible_alias.startswith(current_path):
                    possible_alias = possible_alias[len(current_path)+1:]
                if possible_alias:
                    action_url = fti.queryMethodID(possible_alias,
                                                   default = action_url,
                                                   context = context)
        except AttributeError:
            # Don't raise if we don't have CMF 1.5
            pass

        # XXX: Is there a better way to check this?
        if not action_url.startswith('string:'):
            action_url = 'string:%s' % (action_url,)
        return TraverseTo.TraverseTo(action_url)(controller_state)

registerFormAction('traverse_to_action',
                   factory,
                   'Traverse to the action specified in the argument (a TALES expression) for the current context object (e.g. string:view)')
