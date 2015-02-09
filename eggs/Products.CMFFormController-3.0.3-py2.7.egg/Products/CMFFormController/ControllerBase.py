import os
from Acquisition import aq_base, aq_inner
from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.CMFCore.permissions import View, ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.FSMetadata import FSMetadata, CMFConfigParser
from FormAction import FormAction, FormActionContainer
from FormValidator import FormValidator, FormValidatorContainer
from globalVars import ANY_CONTEXT, ANY_BUTTON
from utils import log

class ControllerBase:
    """Common functions for objects controlled by portal_form_controller"""

    security = ClassSecurityInfo()
    security.declareObjectProtected(View)

    security.declareProtected(ManagePortal, 'manage_formActionsForm')
    manage_formActionsForm = PageTemplateFile('www/manage_formActionsForm', globals())
    manage_formActionsForm.__name__ = 'manage_formActionsForm'

    security.declareProtected(ManagePortal, 'manage_formValidatorsForm')
    manage_formValidatorsForm = PageTemplateFile('www/manage_formValidatorsForm', globals())
    manage_formValidatorsForm.__name__ = 'manage_formValidatorsForm'

    def _updateActions(self, container, old_id, new_id, move):
        """Copy action overrides stored in portal_form_controller from one
        object id to another"""
        actions = container.getFiltered(object_id=old_id)
        for a in actions:
            # if not container.match(new_id, a.getStatus(), a.getContextType(), a.getButton()):
            container.set(FormAction(new_id, a.getStatus(), a.getContextType(),
                           a.getButton(), a.getActionType(), a.getActionArg()))
        if move:
            for a in actions:
                container.delete(a.getKey())

    def _updateValidators(self, container, old_id, new_id, move):
        """Copy validator overrides stored in portal_form_controller from one
        object id to another"""
        validators = container.getFiltered(object_id=old_id)
        for v in validators:
            # if not container.match(new_id, v.getContextType(), v.getButton()):
            container.set(FormValidator(new_id, v.getContextType(), v.getButton(), v.getValidators()))
        if move:
            for v in validators:
                container.delete(v.getKey())

    def _base_notifyOfCopyTo(self, container, op=0):
        self._old_id = self.getId()
        if op==0:  # copy
            self._cloned_object_path = self.getPhysicalPath()

    def _fixup_old_ids(self, old_id):
        fc = getToolByName(self, 'portal_form_controller')
        id = self.getId()
        if old_id != id:
            if hasattr(aq_base(self), 'actions'):
                self._updateActions(self.actions, old_id, id, move=1) # swap the ids for the default actions
                self._updateActions(fc.actions, old_id, id, move=0) # copy the overrides
            if hasattr(aq_base(self), 'validators'):
                self._updateValidators(self.validators, old_id, id, move=1) # swap the ids for the default validators
                self._updateValidators(fc.validators, old_id, id, move=0) # copy the overrides

    def _base_manage_afterAdd(self, object, container):
        old_id = getattr(self, '_old_id', None)
        if old_id:
            self._fixup_old_ids(old_id)
            delattr(self, '_old_id')

    def _base_manage_afterClone(self, object):
        # clean up the old object
        cloned_object_path = getattr(self, '_cloned_object_path')
        cloned_object = self.getPhysicalRoot().unrestrictedTraverse(cloned_object_path)
        delattr(cloned_object, '_old_id')
        delattr(cloned_object, '_cloned_object_path')
        # clean up the new object
        delattr(self, '_cloned_object_path')

    security.declareProtected(ManagePortal, 'listActionTypes')
    def listActionTypes(self):
        """Return a list of available action types."""
        return getToolByName(self, 'portal_form_controller').listActionTypes()

    security.declareProtected(ManagePortal, 'listFormValidators')
    def listFormValidators(self, override, **kwargs):
        """Return a list of existing validators.  Validators can be filtered by
           specifying required attributes via kwargs"""
        controller = getToolByName(self, 'portal_form_controller')
        if override:
            return controller.validators.getFiltered(**kwargs)
        else:
            return self.validators.getFiltered(**kwargs)


    security.declareProtected(ManagePortal, 'listFormActions')
    def listFormActions(self, override, **kwargs):
        """Return a list of existing actions.  Actions can be filtered by
           specifying required attributes via kwargs"""
        controller = getToolByName(self, 'portal_form_controller')
        if override:
            return controller.actions.getFiltered(**kwargs)
        else:
            return self.actions.getFiltered(**kwargs)


    security.declareProtected(ManagePortal, 'listContextTypes')
    def listContextTypes(self):
        """Return list of possible types for template context objects"""
        return getToolByName(self, 'portal_form_controller').listContextTypes()


    security.declareProtected(ManagePortal, 'manage_editFormValidators')
    def manage_editFormValidators(self, REQUEST):
        """Process form validator edit form"""
        controller = getToolByName(self, 'portal_form_controller')
        if REQUEST.form.get('override', 0):
            container = controller.validators
        else:
            container = self.validators
        controller._editFormValidators(container, REQUEST)
        return REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_formValidatorsForm')


    security.declareProtected(ManagePortal, 'manage_addFormValidators')
    def manage_addFormValidators(self, REQUEST):
        """Process form validator add form"""
        controller = getToolByName(self, 'portal_form_controller')
        if REQUEST.form.get('override', 0):
            container = controller.validators
        else:
            container = self.validators
        controller._addFormValidators(container, REQUEST)
        return REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_formValidatorsForm')


    security.declareProtected(ManagePortal, 'manage_delFormValidators')
    def manage_delFormValidators(self, REQUEST):
        """Process form validator delete form"""
        controller = getToolByName(self, 'portal_form_controller')
        if REQUEST.form.get('override', 0):
            container = controller.validators
        else:
            container = self.validators
        controller._delFormValidators(container, REQUEST)
        return REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_formValidatorsForm')


    security.declareProtected(ManagePortal, 'manage_editFormActions')
    def manage_editFormActions(self, REQUEST):
        """Process form action edit form"""
        controller = getToolByName(self, 'portal_form_controller')
        if REQUEST.form.get('override', 0):
            container = controller.actions
        else:
            container = self.actions
        controller._editFormActions(container, REQUEST)
        return REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_formActionsForm')


    security.declareProtected(ManagePortal, 'manage_addFormAction')
    def manage_addFormAction(self, REQUEST):
        """Process form action add form"""
        controller = getToolByName(self, 'portal_form_controller')
        if REQUEST.form.get('override', 0):
            container = controller.actions
        else:
            container = self.actions
        controller._addFormAction(container, REQUEST)
        return REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_formActionsForm')


    security.declareProtected(ManagePortal, 'manage_delFormActions')
    def manage_delFormActions(self, REQUEST):
        """Process form action delete form"""
        controller = getToolByName(self, 'portal_form_controller')
        if REQUEST.form.get('override', 0):
            container = controller.actions
        else:
            container = self.actions
        controller._delFormActions(container, REQUEST)
        return REQUEST.RESPONSE.redirect(self.absolute_url()+'/manage_formActionsForm')


    def getNext(self, controller_state, REQUEST):
        id = self.getId()
        status = controller_state.getStatus()
        context = controller_state.getContext()
        context_base = aq_base(context)

        context_type = getattr(context_base, 'portal_type', None)
        if context_type is None:
            context_type = getattr(context_base, '__class__', None)
            if context_type:
                context_type = getattr(context_type, '__name__', None)

        button = controller_state.getButton()
        controller = getToolByName(aq_inner(self), 'portal_form_controller')

        next_action = None
        try:
            next_action = controller.getAction(id, status, context_type, button)
        except ValueError:
            pass
        if next_action is None:
            try:
                if getattr(context_base, 'formcontroller_actions', None) is not None:
                    next_action = context.formcontroller_actions.match(id, status, context_type, button)
            except ValueError:
                pass
        if next_action is None:
            try:
                next_action = self.actions.match(id, status, context_type, button)
            except ValueError:
                pass
            if next_action is None:
                next_action = controller_state.getNextAction()
                if next_action is None:
                    # default for failure is to traverse to the form
                    if status == 'failure':
                        next_action=FormAction(id, status, ANY_CONTEXT, ANY_BUTTON, 'traverse_to', 'string:%s' % id, controller)
                    if next_action is None:
                        metadata_actions = [str(a) for a in self.actions.getFiltered(object_id=id)]
                        zmi_actions = [str(a) for a in controller.actions.getFiltered(object_id=id)]
                        raise ValueError, 'No next action found for %s.%s.%s.%s\nMetadata actions:\n%s\n\nZMI actions:\n%s\n' % \
                            (id, status, context_type, button, '\n'.join(metadata_actions), '\n'.join(zmi_actions))

        REQUEST.set('controller_state', controller_state)
        return next_action.getAction()(controller_state)


    def getButton(self, controller_state, REQUEST):
        buttons = []
        for k in REQUEST.form.keys():
            if k.startswith('form.button.'):
                buttons.append(k)
        if buttons:
            # Clicking on an image button results in 2 button variables in REQUEST.form
            # (maybe 3),namely form.button.button_name.x, form.button.button_name.y, and
            # possibly form.button.button_name (not for IE, though)
            # If we see more than one key with the button prefix, try to handle sensibly.
            if len(buttons) > 1:
                buttons.sort(lambda x, y: cmp(len(x), len(y)))
                if buttons[0].endswith('.x') or buttons[0].endswith('.y'):
                    buttons[0] = buttons[0][:-2]
            button = buttons[0][len('form.button.'):]
            controller_state.setButton(button)
        return controller_state


    def getValidators(self, controller_state, REQUEST):
        controller = getToolByName(self, 'portal_form_controller')
        context = controller_state.getContext()
        context_type = controller._getTypeName(context)
        button = controller_state.getButton()

        validators = None
        try:
            validators = controller.validators.match(self.id, context_type, button)
            if validators is not None:
                return validators
        except ValueError:
            pass
        try:
            if hasattr(aq_base(context), 'formcontroller_validators'):
                validators = context.formcontroller_validators.match(self.id, context_type, button)
                if validators is not None:
                    return validators
        except ValueError:
            pass
        try:
            validators = self.validators.match(self.id, context_type, button)
            if validators is not None:
                return validators
        except ValueError:
            pass
        return FormValidator(self.id, ANY_CONTEXT, ANY_BUTTON, [])


    def _read_action_metadata(self, id, filepath):
        self.actions = FormActionContainer()

        metadata = FSMetadata(filepath)
        cfg = CMFConfigParser()
        if os.path.exists(filepath + '.metadata'):
            cfg.read(filepath + '.metadata')
            _buttons_for_status = {}

            actions = metadata._getSectionDict(cfg, 'actions')
            if actions is None:
                actions = {}

            for (k, v) in actions.items():
                # action.STATUS.CONTEXT_TYPE.BUTTON = ACTION_TYPE:ACTION_ARG
                component = k.split('.')
                while len(component) < 4:
                    component.append('')
                if component[0] != 'action':
                    raise ValueError, '%s: Format for .metadata actions is action.STATUS.CONTEXT_TYPE.BUTTON = ACTION_TYPE:ACTION_ARG (not %s)' % (filepath, k)
                act = v.split(':',1)
                while len(act) < 2:
                    act.append('')

                context_type = component[2]
                self.actions.set(FormAction(id, component[1], component[2], component[3], act[0], act[1]))

                status_key = str(component[1])+'.'+str(context_type)
                if _buttons_for_status.has_key(status_key):
                    _buttons_for_status[status_key].append(component[3])
                else:
                    _buttons_for_status[status_key] = [component[3]]

            for (k, v) in _buttons_for_status.items():
                if v and not '' in v:
                    sk = k.split('.')
                    status = sk[0]
                    content_type = sk[1]
                    if not status:
                        status = 'ANY'
                    if not content_type:
                        content_type = 'ANY'
                    log('%s: No default action specified for status %s, content type %s.  Users of IE can submit pages using the return key, resulting in no button in the REQUEST.  Please specify a default action for this case.' % (str(filepath), status, content_type))


    def _read_validator_metadata(self, id, filepath):
        self.validators = FormValidatorContainer()

        metadata = FSMetadata(filepath)
        cfg = CMFConfigParser()
        if os.path.exists(filepath + '.metadata'):
            cfg.read(filepath + '.metadata')
            _buttons_for_status = {}

            validators = metadata._getSectionDict(cfg, 'validators')
            if validators is None:
                validators = {}
            for (k, v) in validators.items():
                # validators.CONTEXT_TYPE.BUTTON = LIST
                component = k.split('.')
                while len(component) < 3:
                    component.append('')
                if component[0] != 'validators':
                    raise ValueError, '%s: Format for .metadata validators is validators.CONTEXT_TYPE.BUTTON = LIST (not %s)' % (filepath, k)

                context_type = component[1]
                self.validators.set(FormValidator(id, component[1], component[2], v))

                status_key = str(context_type)
                if _buttons_for_status.has_key(status_key):
                    _buttons_for_status[status_key].append(component[2])
                else:
                    _buttons_for_status[status_key] = [component[2]]

            for (k, v) in _buttons_for_status.items():
                if v and not '' in v:
                    content_type = k
                    if not content_type:
                        content_type = 'ANY'
                    log('%s: No default validators specified for content type %s.  Users of IE can submit pages using the return key, resulting in no button in the REQUEST.  Please specify default validators for this case.' % (str(filepath), content_type))


    security.declarePublic('writableDefaults')
    def writableDefaults(self):
        """Can default actions and validators be modified?"""
        return 1

InitializeClass(ControllerBase)
