from zope.interface.declarations import moduleProvides
from zope.globalrequest.interfaces import IGlobalRequest

moduleProvides(IGlobalRequest)


from zope.globalrequest.local import getLocal, setLocal


def getRequest():
    """ return the currently active request object """
    return getLocal('request')


def setRequest(request):
    """ set the request object to be returned by `getRequest` """
    setLocal('request', request)


def clearRequest():
    """ clear the stored request object """
    setRequest(None)

