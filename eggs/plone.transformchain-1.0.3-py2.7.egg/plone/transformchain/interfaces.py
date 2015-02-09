from zope.interface import Interface
from zope import schema

try:
    from repoze.zope2.interfaces import ITransformer as IBaseTransformer
except ImportError:
    IBaseTransformer = Interface

DISABLE_TRANSFORM_REQUEST_KEY = 'plone.transformchain.disable'

class ITransform(Interface):
    """Register a named multi adapter from (published, request,) to
    this interface to change the response.

    ``published`` is the published object, i.e. the last thing being traversed
    to. Typically, it will be a view.

    ``request`` is the request type.

    To control the order of transforms, use the 'order' attribute. It may be
    positive or negative.
    """

    order = schema.Int(title=u"Order")

    def transformUnicode(result, encoding):
        """Called to allow the transformer to modify the result if the result
        is a unicode string.

        Return a new unicode string, encoded string or iterable.

        Return None to indicate that the response should not be modified.
        """

    def transformBytes(result, encoding):
        """Called to allow the transformer to modify the result if the result
        is an encoded string.

        Return a new unicode string, encoded string or iterable.

        Return None to indicate that the response should not be modified.
        """

    def transformIterable(result, encoding):
        """Called to allow the transformer to modify the result if the result
        is an iterable of strings (as per the WSGI specification).

        Return a new unicode string, encoded string or iterable.

        Return None to indicate that the response should not be modified.
        """

class ITransformer(IBaseTransformer):
    """Low-level hook. This interface is defined in repoze.zope2, but since
    this package can be used with the classic ZPublisher as well, we redefine
    it here. You probably don't want to use this directly; you want to use
    ITransform instead.
    """

    def __call__(request, result, encoding):
        """Return a modified result.

        `request` is the Zope request. Response headers may be read or
        modified in `request.response`.

        `result` is an iterable of byte strings that represents the response
        body. When unwound, its contents will match the response content type.

        `encoding` is the default encoding used.

        Return the new result iterable, or a string. If a string is returned,
        the Content-Type header will be updated automatically. If a unicode
        string is returned, it will be encoded with the current content
        encoding.

        Do not call `request.response.setBody()`. It will have no effect.
        """
