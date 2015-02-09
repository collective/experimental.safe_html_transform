## Script (Python) "mail_password"
##title=Mail a user's password
##parameters=
REQUEST=context.REQUEST
return context.portal_registration.mailPassword(REQUEST['userid'], REQUEST)
