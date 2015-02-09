from zope import interface

from zope.publisher.browser import isCGI_NAME
from zope.publisher.interfaces.browser import IBrowserApplicationRequest

from zope.i18n.interfaces import IUserPreferredCharsets

import z3c.form.interfaces

class IFixedUpRequest(interface.Interface):
    """Marker interface used to ensure we don't fix up the request twice
    """

class IProcessedRequest(interface.Interface):
    """Marker interface used to ensure we don't process the request inputs
    twice.
    """

# Safer versions of the functions in Products.Five.browser.decode

def processInputs(request, charsets=None):
    """Process the values in request.form to decode strings to unicode, using
    the passed-in list of charsets. If none are passed in, look up the user's
    preferred charsets. The default is to use utf-8.
    """

    if IProcessedRequest.providedBy(request):
        return

    if charsets is None:
        envadapter = IUserPreferredCharsets(request, None)
        if envadapter is None:
            charsets = ['utf-8']
        else:
            charsets = envadapter.getPreferredCharsets() or ['utf-8']

    for name, value in request.form.items():
        if not (isCGI_NAME(name) or name.startswith('HTTP_')):
            if isinstance(value, str):
                request.form[name] = _decode(value, charsets)
            elif isinstance(value, (list, tuple,)):
                newValue = []
                for val in value:
                    if isinstance(val, str):
                        val = _decode(val, charsets)
                    newValue.append(val)

                if isinstance(value, tuple):
                    newValue = tuple(value)

                request.form[name] = newValue

    interface.alsoProvides(request, IProcessedRequest)

def _decode(text, charsets):
    for charset in charsets:
        try:
            text = unicode(text, charset)
            break
        except UnicodeError:
            pass
    return text

def switch_on(view, request_layer=z3c.form.interfaces.IFormLayer):
    """Fix up the request and apply the given layer. This is mainly useful
    in Zope < 2.10 when using a wrapper layout view.
    """

    request = view.request

    if (not IFixedUpRequest.providedBy(request) and
        not IBrowserApplicationRequest.providedBy(request)
    ):

        interface.alsoProvides(request, IFixedUpRequest)
        interface.alsoProvides(request, request_layer)
