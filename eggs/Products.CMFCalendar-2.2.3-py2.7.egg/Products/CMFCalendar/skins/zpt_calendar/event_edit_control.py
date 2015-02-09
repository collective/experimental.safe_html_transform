##parameters=title=None, description=None, event_type=None, effectiveDay=None, effectiveMo=None, effectiveYear=None, expirationDay=None, expirationMo=None, expirationYear=None, start_time=None, startAMPM=None, stop_time=None, stopAMPM=None, location=None, contact_name=None, contact_email=None, contact_phone=None, event_url=None, **kw
##
from Products.CMFCalendar.exceptions import ResourceLockedError
from Products.CMFCalendar.utils import Message as _

try:
    context.edit(title, description, event_type, effectiveDay, effectiveMo,
                 effectiveYear, expirationDay, expirationMo, expirationYear,
                 start_time, startAMPM, stop_time, stopAMPM, location,
                 contact_name, contact_email, contact_phone, event_url)
    return context.setStatus(True, _(u'Event changed.'))
except ResourceLockedError, errmsg:
    return context.setStatus(False, errmsg)
