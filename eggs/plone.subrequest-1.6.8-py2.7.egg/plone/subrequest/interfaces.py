from zope.publisher.interfaces.browser import IBrowserRequest

class ISubRequest(IBrowserRequest):
    """Marker for sub-requests.
    """
