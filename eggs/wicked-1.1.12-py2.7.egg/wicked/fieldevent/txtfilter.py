from wicked.fieldevent.interfaces import ITxtFilter, IField
from wicked.fieldevent.interfaces import ITxtFilterList, EndFiltrationException
from wicked import utils
from zope.component import queryMultiAdapter, subscribers
from zope.interface import implements
from interfaces import ITxtFilter


def txtfilter_output(field, instance, event):
    """a run once subscriber to process text in a pipeline"""

    if getattr(event, '_txtfiltered_', False):
        return

    filter_names = queryMultiAdapter((field, instance, event), ITxtFilterList)
    if not filter_names:
        return

    txts = subscribers((field, instance, event), ITxtFilter)
    txtmap = dict([(f.name, f) for f in txts])

    for name in filter_names:
        try:
            txtfilter = txtmap.get(name, None)
            if callable(txtfilter):
                txtfilter()
        except EndFiltrationException, e:
            break

    event._txtfiltered_=True


class TxtFilter(object):
    """Abstract Base for Filtration
    """
    implements(ITxtFilter)

    name = None    # required
    pattern = None

    def __init__(self, field, context, event):
        self.context = context
        self.field = field
        self.event = event

    @utils.memoize
    def findall(self, value):
        for pattern in self.patterns:
            val = pattern.findall(value)
            if len(val):
                return val
        return val

    @utils.memoizedproperty
    def patterns(self):
        if not isinstance(self.pattern, list):
            return [self.pattern]
        return self.pattern

    @utils.memoizedproperty
    def chunks(self):
        """Simple text replacement via co-op with the modules"""
        for pattern in self.patterns:
            val=pattern.split(self.event.value)
            if len(val)>1:
                return val
        return val

    @utils.memoizedproperty
    def dynamic(self):
        """tricky ben saller split"""
        return self.chunks[1::2]

    @utils.memoizedproperty
    def filtered_chunks(self):
        return [self._filterCore(d, **self.event.kwargs) for d in self.dynamic]

    @property
    def filtered_text(self):
        """join the two lists (knowing that len(text) == subs+1)"""
        return ''.join(ijoin(self.chunks[::2], self.filtered_chunks))

    def __call__(self):
        if len(self.chunks) == 1: # fastpath
            return

        # set value reference (accessing filtered_text does the work)
        self.event.value = self.filtered_text

    def _filterCore(self,  chunk, **kwargs):
        """Subclasses override this to provide specific impls"""
        return ''


def ijoin(a,b):
    """yield a0,b0,a1,b1.. if len(a) = len(b)+1"""
    yield(a[0])
    for i in range(1,len(a)):
        yield(b[i-1])
        yield(a[i])
