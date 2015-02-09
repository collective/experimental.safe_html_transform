##parameters=thisDay, event

# Returns a string to represent the event

from DateTime import DateTime

text = ""

last_date=DateTime(thisDay.Date()+" 23:59:59")

if event.end > last_date:
  return event.end.aCommon()[:12]
else:
  return event.end.TimeMinutes()

