# -*- coding: utf8 -*-

from zope.interface import implements
from plone.app.querystring.interfaces import IParsedQueryIndexModifier


class SimpleFooIndexModifier(object):
    """Test simple index modifier that do nothing"""

    implements(IParsedQueryIndexModifier)

    def __call__(self, value):
        raise Exception("SimpleFooIndexModifier has been called!")


class TitleFooIndexModifier(object):
    """Test index modifier that check always Foo"""

    implements(IParsedQueryIndexModifier)

    def __call__(self, value):
        return ('Title', 'Foo')


class AbstractToDescriptionIndexModifier(object):
    """
    Test index modifier that translate "Abstract" to Description index
    but where value do not count letter "e"
    """

    implements(IParsedQueryIndexModifier)

    def __call__(self, value):
        value['query'] = value['query'].replace('e', '')
        return ('Description', value)
