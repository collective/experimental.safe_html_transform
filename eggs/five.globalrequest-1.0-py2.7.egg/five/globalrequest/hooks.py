from zope.globalrequest import setRequest, clearRequest

def set_(event):
    setRequest(event.request)

def clear(event):
    clearRequest()
