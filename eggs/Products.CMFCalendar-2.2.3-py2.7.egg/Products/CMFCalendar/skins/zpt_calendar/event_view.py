##parameters=
##
from Products.CMFDefault.utils import decode

options = {}
options['title'] = context.Title()
options['description'] = context.Description()
options['contact_name'] = context.contact_name
options['location'] = context.location
options['contact_email'] = context.contact_email
options['event_types'] = context.Subject()
options['contact_phone'] = context.contact_phone
options['event_url'] = context.event_url
start = context.start()
options['start_date'] = DateTime.Date(start)
options['start_time'] = DateTime.Time(start)
stop = context.end()
options['stop_date'] = DateTime.Date(stop)
options['stop_time'] = DateTime.Time(stop)

return context.event_view_template(**decode(options, script))
