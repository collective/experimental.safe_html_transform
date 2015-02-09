try:
    from plone.supermodel.exportimport import BaseHandler
    HAVE_SUPERMODEL = True
except ImportError:
    HAVE_SUPERMODEL = False

if HAVE_SUPERMODEL:

    from zope.interface import implements
    from zope.component import adapts
    from plone.app.textfield import RichText
    from plone.supermodel.interfaces import IToUnicode
    from plone.app.textfield.interfaces import IRichText


    class RichTextHandler_(BaseHandler):
        """Special handling for the RichText field, to deal with 'default'
        that may be unicode.
        """

        # Don't read or write 'schema'
        filteredAttributes = BaseHandler.filteredAttributes.copy()
        filteredAttributes.update({'schema': 'rw'})

        def __init__(self, klass):
            super(RichTextHandler_, self).__init__(klass)


    class RichTextToUnicode(object):
        implements(IToUnicode)
        adapts(IRichText)

        def __init__(self, context):
            self.context = context

        def toUnicode(self, value):
            return value.raw

    RichTextHandler = RichTextHandler_(RichText)
