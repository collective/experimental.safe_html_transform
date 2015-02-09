## Script (Python) "validate_password"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##bind state=state
##parameters=userid=None, password=None, password2=None
##title=Validate password

result = failMessage=context.portal_registration.testPasswordValidity(password, password2)
if result:
    state.setError('password', result)

if state.getErrors():
    return state.set(status='failure', portal_status_message='Please correct the indicated errors.')
else:
    return state
