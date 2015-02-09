from wicked import utils
from wicked.at.seeker import IWickedQuery, AdvQueryMatchingSeeker
from wicked.cache import ICacheManager, ContentCacheManager
from wicked.fieldevent.interfaces import IFieldRenderEvent, IFieldStorageEvent
from wicked.fieldevent.interfaces import IFieldValueSetter
from wicked.interfaces import IAmWicked
from wicked.interfaces import IAmWickedField
from wicked.interfaces import IWickedEvent
from wicked.interfaces import IWickedFilter
from wicked.txtfilter import BrackettedWickedFilter
from wicked.txtfilter import backlink, brackettedbacklink
from wicked.txtfilter import IAmWickedField, IFieldEvent
from wicked.txtfilter import WickedFilter, IWickedFilter
from wicked.txtfilter import WickedFilter, wicked_listener, bracketted_wicked_listener

from zope.component import getSiteManager
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleVocabulary

import logging
logger = logging.getLogger('wicked.registration')

class BaseWickedRegistration(object):
    """abstract base: add a docstring to display a description on the
    wicked dashboard"""
    title = "((Basic))"
    field = IAmWickedField
    content = IAmWicked
    event = IFieldRenderEvent
    txtfilter = WickedFilter
    txtfilter_provides = IWickedFilter
    subscriber = (wicked_listener,)

    def __init__(self, context, **kw):
        self.site = context
        for key, item in kw.items():
            if hasattr(self, key):
                setattr(self, key, item)

    @utils.memoizedproperty
    def sm(self):
        return getSiteManager(self.site)

    @property
    def required(self):
        return (self.field, self.content, self.event)

    def handle(self, unregister=False):
        # @@ add logging
        handle_adapter_reg = self.sm.registerAdapter
        handle_subscriber_reg = self.sm.registerHandler
        handle_sub_adapter_reg = self.sm.registerSubscriptionAdapter
        if unregister:
            handle_adapter_reg = self.sm.unregisterAdapter
            handle_subscriber_reg = self.sm.unregisterHandler
            handle_sub_adapter_reg = self.sm.unregisterSubscriptionAdapter

        self.handle_txtfilter(handle_adapter_reg)
        for subscriber in self.subscriber:
            handle_subscriber_reg(subscriber, required=self.required)
        for bh in self.backlink_handler:
            handle_sub_adapter_reg(bh)
        return (handle_adapter_reg, handle_subscriber_reg, handle_sub_adapter_reg)

    def handle_txtfilter(self, handle, event=None, txtfilter=None, unregister=False):
        """helper for common reg of txtfilter"""
        txtfilter = txtfilter and txtfilter or self.txtfilter
        required = list(self.required)
        if event:
            required[2] = event

        handle(self.txtfilter,
               required=required,
               provided=self.txtfilter_provides)

    def is_installed(self):
        raise NotImplemented


class BasePloneWickedRegistration(BaseWickedRegistration):
    """Basic wicked behavior for Plone. Registers a fieldevent
    subscriber and the wicked filter."""
    subscriber = (wicked_listener, bracketted_wicked_listener)
    backlink_handler = (backlink, brackettedbacklink)
    #txtfilter = EasyWickedFilter

class BasePloneMediaWickedRegistration(BasePloneWickedRegistration):
    """Same as basic but with square bracket style linking"""
    title = "[[Bracketted]]"
    txtfilter = BrackettedWickedFilter

class SelectiveRegistration(BaseWickedRegistration):
    """by dropping direct registration to IAmWicked for content, we
    can selectively turn on and off the creation of wiki behavior by
    content interface. To do this though, we have to hand register a
    seeker and a cache manager"""
    cache = ContentCacheManager
    cache_provides = ICacheManager
    seeker = AdvQueryMatchingSeeker
    seeker_provides = IWickedQuery
    other_events = (IWickedEvent, IFieldStorageEvent)
    backlink_handler = (backlink, brackettedbacklink)
    subscriber = (wicked_listener, bracketted_wicked_listener)

    @property
    def cache_required(self):
        return (self.txtfilter_provides, self.content)

    def handle(self, unregister=False):
        handle_adapter_reg, handle_subscriber_reg, handle_sub_adapter_reg = super(SelectiveRegistration,
                                       self).handle(unregister=unregister)
        self.handle_cache(handle_adapter_reg)
        self.handle_seeker(handle_adapter_reg)

        for event in self.other_events:
            self.handle_txtfilter(handle_adapter_reg, event=event)
        return (handle_adapter_reg,
                handle_subscriber_reg,
                handle_sub_adapter_reg)

    def handle_cache(self, handle):
        handle(self.cache,
               required=self.cache_required,
               provided=self.cache_provides)

    def handle_seeker(self, handle):
        handle(self.seeker,
               required=(self.content,),
               provided=self.seeker_provides)

## vocabulary

# @@ this will have to wait since plone does not have an egg story yet

class BaseConfigurationOptionsFactory(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
##         entry_points = get_points("wicked.base_registration")
##         items = [(bc.name, bc.load().title) for bc in entry_points]
##         items.sort()
##         items.insert(0, ('off', 'Off'))
##         return SimpleVocabulary.fromItems(items)
        pass

class CacheConfigurationOptionsFactory(object):
    implements(IVocabularyFactory)

    def __call__(self, context):
        return SimpleVocabulary.fromItems(list())


CacheConfigurationOptions = CacheConfigurationOptionsFactory()
BaseConfigurationOptions = BaseConfigurationOptionsFactory()

