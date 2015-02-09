import logging

from zope.interface import implements
from zope.component.hooks import getSite
from Products.CMFPlone.utils import safe_unicode
from plone.app.textfield.interfaces import IRichTextValue, ITransformer
from persistent import Persistent

LOG = logging.getLogger('plone.app.textfield')


class RawValueHolder(Persistent):
    """Place the raw value in a separate persistent object so that it does not
    get loaded when all we want is the output.
    """

    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return u"<RawValueHolder: %s>" % self.value


class RichTextValue(object):
    """The actual value.

    Note that this is not a persistent object, to avoid a separate ZODB object
    being loaded.
    """

    implements(IRichTextValue)

    def __init__(self, raw=None, mimeType=None, outputMimeType=None, encoding='utf-8', output=None):
        self._raw_holder = RawValueHolder(raw)
        self._mimeType = mimeType
        self._outputMimeType = outputMimeType
        self._encoding = encoding
    # the raw value - stored in a separate persistent object

    @property
    def raw(self):
        return self._raw_holder.value
    # Encoded raw value

    @property
    def encoding(self):
        return self._encoding

    @property
    def raw_encoded(self):
        if self._raw_holder.value is None:
            return ''
        happy_value = safe_unicode(self._raw_holder.value,
                                   encoding=self.encoding)
        return happy_value.encode(self.encoding, 'ignore')

    # the current mime type
    @property
    def mimeType(self):
        return self._mimeType
    # the default mime type

    @property
    def outputMimeType(self):
        return self._outputMimeType

    @property
    def output(self):
        site = getSite()
        return self.output_relative_to(site)

    def output_relative_to(self, context):
        """Transforms the raw value to the output mimetype, within a specified context.

        If the value's mimetype is already the same as the output mimetype,
        no transformation is performed.

        The context parameter is relevant when the transformation is
        context-dependent. For example, Plone's resolveuid-and-caption
        transform converts relative links to absolute links using the context
        as a base.

        If a transformer cannot be found for the specified context, a
        transformer with the site as a context is used instead.
        """
        if self.mimeType == self.outputMimeType:
            return self.raw_encoded

        transformer = ITransformer(context, None)
        if transformer is None:
            site = getSite()
            transformer = ITransformer(site, None)
            if transformer is None:
                return None

        return transformer(self, self.outputMimeType)

    def __repr__(self):
        return u"RichTextValue object. (Did you mean <attribute>.raw or <attribute>.output?)"
