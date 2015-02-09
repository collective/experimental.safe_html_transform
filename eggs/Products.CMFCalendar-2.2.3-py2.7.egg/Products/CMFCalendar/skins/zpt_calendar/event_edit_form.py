##parameters=change='', change_and_view=''
##
from Products.CMFCalendar.utils import Message as _
from Products.CMFDefault.utils import decode

form = context.REQUEST.form
if change and \
        context.event_edit_control(**form) and \
        context.setRedirect(context, 'object/edit'):
    return
elif change_and_view and \
        context.event_edit_control(**form) and \
        context.setRedirect(context, 'object/view'):
    return


options = {}

options['title'] = form.get('title', context.Title())
options['description'] = form.get('description', context.Description())
options['contact_name'] = form.get('contact_name', context.contact_name)
options['location'] = form.get('location', context.location)
options['contact_email'] = form.get('contact_email', context.contact_email)
options['event_type'] = form.get('event_type', context.Subject())
options['contact_phone'] = form.get('contact_phone', context.contact_phone)
options['event_url'] = form.get('event_url', context.event_url)

date_strings = context.getStartStrings()
options['effectiveYear'] = form.get('effectiveYear', date_strings['year'])
options['effectiveMo'] = form.get('effectiveMo', date_strings['month'])
options['effectiveDay'] = form.get('effectiveDay', date_strings['day'])

time_strings = context.getStartTimeString().split()
options['start_time'] = form.get('start_time', time_strings[0])
AMPM = (len(time_strings) == 2 and time_strings[1] or 'pm')
options['startAMPM'] = form.get('startAMPM', AMPM)

date_strings = context.getEndStrings()
options['expirationYear'] = form.get('expirationYear', date_strings['year'])
options['expirationMo'] = form.get('expirationMo', date_strings['month'])
options['expirationDay'] = form.get('expirationDay', date_strings['day'])

time_strings = context.getStopTimeString().split()
options['stop_time'] = form.get('stop_time', time_strings[0])
AMPM = (len(time_strings) == 2 and time_strings[1] or 'pm')
options['stopAMPM'] = form.get('stopAMPM', AMPM)

buttons = []
target = context.getActionInfo('object/edit')['url']
buttons.append( {'name': 'change', 'value': _(u'Change')} )
buttons.append( {'name': 'change_and_view', 'value': _(u'Change and View')} )
options['form'] = { 'action': target,
                    'listButtonInfos': tuple(buttons) }

return context.event_edit_template(**decode(options, script))
