##parameters=thisDay, event

# Returns a string to represent the start of the event

from DateTime import DateTime

first_date=DateTime(thisDay.Date()+" 00:00:00")

if event.start < first_date:
  return event.start.aCommon()[:12]
else:
  return event.start.TimeMinutes()
