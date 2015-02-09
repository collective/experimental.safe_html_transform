import logging

from zope.interface import implements
from zope.component import getAdapters

from plone.transformchain.interfaces import ITransform, ITransformer
from plone.transformchain.interfaces import DISABLE_TRANSFORM_REQUEST_KEY

from ZODB.POSException import ConflictError
from ZServer.FTPRequest import FTPRequest

def sort_key(a, b):
    return cmp(a.order, b.order)

LOGGER = logging.getLogger('plone.transformchain')

class Transformer(object):
    """Delegate the opportunity to transform the response to multiple,
    ordered adapters.
    """

    implements(ITransformer)

    def __call__(self, request, result, encoding):


        # Don't transform FTP requests
        if isinstance(request, FTPRequest):
            return None

        # Off switch
        if request.environ.get(DISABLE_TRANSFORM_REQUEST_KEY, False):
            return None

        try:
            published = request.get('PUBLISHED', None)

            handlers = [v[1] for v in getAdapters((published, request,), ITransform)]
            handlers.sort(sort_key)

            for handler in handlers:

                if isinstance(result, unicode):
                    newResult = handler.transformUnicode(result, encoding)
                elif isinstance(result, str):
                    newResult = handler.transformBytes(result, encoding)
                else:
                    newResult = handler.transformIterable(result, encoding)

                if newResult is not None:
                    result = newResult

            return result
        except ConflictError:
            raise
        except Exception, e:
            LOGGER.exception(u"Unexpected error whilst trying to apply transform chain")
