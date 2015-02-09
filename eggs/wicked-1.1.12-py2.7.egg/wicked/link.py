from wicked import utils
from wicked.interfaces import IWickedLink, IWickedEvent, WickedContentAddedEvent
from zope.component import handle, adapter
from zope.event import notify
from zope.interface import implements

_marker=object()

class WickedAdd(object):

    def __init__(self, context, request):
        self.context = context
        self._context = (context,)
        self.request = request

    def notify_content_added(self, newcontent, title, section):
        notify(WickedContentAddedEvent(self.context, newcontent, title, section, self.request))

    def add_content(self, title=None, section=None, type_name=_marker):
        raise NotImplementedError

    def addMenu(self):
        return 1


_marker=object()

class BasicLink(object):
    implements(IWickedLink)
    section = _marker

    def __init__(self, context, request):
        self.context = context
        self._context = (context,)
        self.request = request
        self.counter=utils.counter()

    @utils.memoizedproperty
    def howmany(self):
        return len(self.links)

    @utils.memoizedproperty
    def multiple(self):
        return self.howmany > 1

    @utils.memoizedproperty
    def links(self):
        """
        calculates urls

        abstract zope2ism
        """
        for link in self._links:
            link['url'] = self.request.physicalPathToURL(link['path'], 0)
        return self._links

    @property
    def singlelink(self):
        return self.links[0]

    @property
    def count(self):
        return self.counter.next()

    @utils.clearbefore
    def load(self, links, chunk):
        self._links = links
        self.chunk = chunk


@adapter(IWickedEvent)
def redispatch(event):
    handle(event.context, event)


def test_suite():
    import unittest
    from zope.testing import doctest
    suite = doctest.DocFileSuite('link.txt',
                                 globs=globals(),
                                 package='wicked',
                                 optionflags=doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS)
    return suite
