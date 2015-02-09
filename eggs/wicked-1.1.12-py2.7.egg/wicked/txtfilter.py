##########################################################
#
# Licensed under the terms of the GNU Public License
# (see docs/LICENSE.GPL)
#
# Copyright (c) 2005:
#   - The Open Planning Project (http://www.openplans.org/)
#   - Whit Morriss <whit@kalistra.com>
#   - Rob Miller <rob@kalistra.com> (RaFromBRC)
#   - and contributors
#
##########################################################
from interfaces import IAmWickedField, IAmWicked, IFieldEvent
from interfaces import ICacheManager, IValueToString, IScope
from interfaces import IWickedFilter, IWickedQuery, IBacklinkManager
from normalize import titleToNormalizedId as normalize
from wicked import utils
from wicked.fieldevent.interfaces import EndFiltrationException
from wicked.fieldevent.interfaces import ITxtFilterList, IFieldRenderEvent
from wicked.fieldevent.interfaces import IFieldValueSetter, IFieldStorageEvent
from wicked.fieldevent.interfaces import IFieldEvent
from zope.component.interfaces import ComponentLookupError
from wicked.fieldevent.txtfilter import TxtFilter
from zope.component import getMultiAdapter, adapts, adapter
from zope.interface import implements, implementer, Interface, alsoProvides

import re

_marker = object()

pattern1 = re.compile(r'\(\(([\w\W]+?)\)\)') # matches ((Some Text To link 123))
pattern2 = re.compile(r'\[\[([\w\W]+?)\]\]') # matches [[Some Text To link 123]]

def removeParens(wikilink):
    wikilink.replace('((', '')
    wikilink.replace('))', '')
    wikilink.replace('[[', '')
    wikilink.replace(']]', '')
    return wikilink

class WickedFilter(TxtFilter):
    implements(IWickedFilter)
    adapts(IAmWickedField, IAmWicked, IFieldEvent)

    name = 'Wicked Filter'

    #pattern = [pattern1, pattern2]
    query_iface = IWickedQuery
    _encoding = 'UTF8'

    def __init__(self, field, instance, event):
        super(WickedFilter, self).__init__(field, instance, event)
        self.section = field.__name__
        self.pattern = None

    @utils.memoizedproperty
    def scope(self):
        try:
            return getMultiAdapter((self.field, self.context), IScope)
        except ComponentLookupError:
            return ''

    # avoid global lookup
    getMatch = staticmethod(utils.getMatch)
    _normalize = staticmethod(normalize)

    # optimization
    @utils.memoize
    def normalize(self, value):
        return self._normalize(value)

    @utils.memoizedproperty
    def encoding(self):
        """AT hack"""
        try:
            encoding = self.context.getCharset()
        except AttributeError:
            encoding = self._encoding
        return encoding

    def _filterCore(self, chunk, **kwargs):
        normalled = self.normalize(chunk)
        links=self.getLinks(chunk, normalled)
        self.renderer.load(links, chunk)
        return self.renderer().encode(self.encoding)

    @property
    def filtered_text(self):
        """syntax preprocessing"""
        return super(WickedFilter, self).filtered_text

    @utils. memoize
    @utils.linkcache
    def getLinks(self, chunk, normalled):
        self.resolver.configure(chunk, normalled, self.scope)
        brains = self.resolver.search
        if not brains:
            brains = self.resolver.scopedSearch
        links = [utils.packBrain(b) for b in brains if b]
        return links

    @utils.memoizedproperty
    def resolver(self):
        """
        @return query object
        """
        return self.query_iface(self.context)

    @utils.memoizedproperty
    def backlinker(self):
        return getMultiAdapter((self, self.context), IBacklinkManager)

    def manageLink(self, obj, link):
        self.backlinker.manageLink(obj, link)

    def unlink(self, uid):
        self.backlinker.unlink(uid)

    def manageLinks(self, links):
        self.backlinker.manageLinks(links)

    @utils.memoizedproperty
    def cache(self):
        return getMultiAdapter((self, self.context), ICacheManager)

    @utils.memoizedproperty
    def renderer(self):
        # @@ better way to get request? maybe a txtfilter should be a view?
        renderer = getMultiAdapter((self.context, self.context.REQUEST), Interface, 'link_renderer')
        renderer.section = self.section
        # hook for zope2 aq wrapper
        if hasattr(renderer, '__of__'):
            return renderer.__of__(self.context)
        return renderer

    def __call__(self):
        if self.event.kwargs.get('raw', False):
            raise EndFiltrationException('Kwargs flag for raw return')
        super(WickedFilter, self).__call__()

##     def removeParens(wikilink):
##         wikilink.replace('((', '')
##         wikilink.replace('))', '')
##         return wikilink
    removeParens=staticmethod(removeParens)


class BrackettedWickedFilter(WickedFilter):
    """media wiki style bracket matching"""
    pattern=pattern2
    def removeParens(wikilink):
        wikilink.replace('[[', '')
        wikilink.replace(']]', '')
        return wikilink
    removeParens=staticmethod(removeParens)

NAME = WickedFilter.name


## event handlers ##

class WickedListener(object):

    def __init__(self, pattern):
        self.pattern = pattern

    def render(self, field, instance, event):
        """standalone wicked filter (ie not as a txtfilter). Optimal if
        not using txtfilters"""

        if event.kwargs.get('raw', False):
            return

        wicked = getMultiAdapter((field, instance, event), IWickedFilter)
        wicked.pattern = self.pattern
        try:
            wicked()
        except EndFiltrationException:
            pass

    def store(self, field, event):
        try:
            wicked = utils.getWicked(field, event.instance, event)
        except ComponentLookupError:
            # no adapter registered for this type currently
            # @@ This might be handle better by redispatch
            return

        wicked.pattern = self.pattern
        if not event.value:
            return

        value = event.value
        value_str = value

        try:
            # this block handle conversions for file uploads and
            # atapi.BaseUnit or any other not quite plain text "value objects"
            value_str = getMultiAdapter((value, field), IValueToString)
        except ComponentLookupError:
            pass

        found = wicked.findall(value_str)

        if not len(found):
            return

        new_links = [wicked.removeParens(link) for link in found]
        wicked.manageLinks(new_links)

from zope.interface import classImplements

@implementer(IFieldValueSetter)
@adapter(IAmWickedField, IFieldStorageEvent)
def backlink_handler(field, event):
    try:
        wicked = utils.getWicked(field, event.instance, event)
    except ComponentLookupError:
        # no adapter registered for this type currently
        # @@ This might be handle better by redispatch
        return

    if not event.value:
        return

    value = event.value
    value_str = value

    try:
        # this block handle conversions for file uploads and
        # atapi.BaseUnit or any other not quite plain text "value objects"
        value_str = getMultiAdapter((value, field), IValueToString)
    except ComponentLookupError:
        pass


    found = wicked.findall(value_str)

    if not len(found):
        return

    new_links = [wicked.removeParens(link) for link in found]
    wicked.manageLinks(new_links)

pattern1_listeners = WickedListener(pattern1)
pattern2_listeners = WickedListener(pattern2)

## hack around fact that functions can not be pickled ##

class wicked_listener(object):
    __init__=staticmethod(pattern1_listeners.render)

class bracketted_wicked_listener(object):
    __init__=staticmethod(pattern2_listeners.render)

class backlink(object):
    implements(IFieldValueSetter)
    adapts(IAmWickedField, IFieldStorageEvent)

    __init__ = staticmethod(pattern1_listeners.store)

BacklinkRegistrationProxy = backlink

class brackettedbacklink(object):
    implements(IFieldValueSetter)
    adapts(IAmWickedField, IFieldStorageEvent)

    __init__ = staticmethod(pattern2_listeners.store)


## toy example code ##

@adapter(IAmWickedField, IAmWicked, IFieldRenderEvent)
@implementer(ITxtFilterList)
def filter_list(field, context, event):
    """example adapter for a one item list for ordering a txtfilter
    pipeline involving wicked only.  Practically useless, for example
    only"""
    return [NAME]
