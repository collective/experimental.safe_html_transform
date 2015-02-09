from zope.i18nmessageid import MessageFactory
from zope.i18n import translate
from zope.i18nmessageid import Message


PloneMessageFactory = MessageFactory('plone')

def safe_unicode(value):
    if isinstance(value, unicode):
        return value
    elif isinstance(value, str):
        try:
            return unicode(value, 'utf-8')
        except UnicodeDecodeError:
            return unicode(value, 'utf-8', 'ignore')
    return str(value)


def recursiveTranslate(message, **kwargs):
    """translates also the message mappings before translating the message.
    if kwargs['REQUEST'] is None, return the message untranslated
    """

    request = kwargs.get('REQUEST',None)

    map = message.mapping
    if map:
        for key in map.keys():
            if type(map[key]) == Message:
                map[key] = translate(map[key], context=request)

    return translate(message, context=request)
