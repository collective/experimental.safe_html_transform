import zope.deferredimport

zope.deferredimport.deprecated(
    "It has been moved to pythongettext.msgfmt. "
    "This alias will be removed in the next PTS version",
    Msgfmt = 'pythongettext.msgfmt:Msgfmt',
    )

zope.deferredimport.deprecated(
    "It has been moved to pythongettext.msgfmt. "
    "This alias will be removed in the next PTS version",
    PoSyntaxError = 'pythongettext.msgfmt:PoSyntaxError',
    )
