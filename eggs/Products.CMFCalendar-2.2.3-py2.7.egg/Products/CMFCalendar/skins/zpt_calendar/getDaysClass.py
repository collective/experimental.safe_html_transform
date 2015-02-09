##parameters=day, month, year, event=None

# Is the date given today?
# If so we want to return a class of 'todayevent' so that the event gets the
# today border around it.
# If not we want to return just 'event' so the event gets the proper shading.

import DateTime

current = DateTime.DateTime()

if current.year()==year and current.month()==month and current.day()==int(day):
  if event:
    return "todayevent"
  else:
    return "todaynoevent"
  
if event:
  return "event"
else:
  return ""