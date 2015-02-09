##########################################################
#
# Licensed under the terms of the GNU Public License
# (see docs/LICENSE.GPL)
#
# Copyright (c) 2005:
#   - The Open Planning Project (http://www.openplans.org/)
#   - Whit Morriss <whit at www.openplans.org>
#   - and contributors
#
##########################################################
from normalize import titleToNormalizedId as normalize
from zope.component import getMultiAdapter
from wicked.interfaces import IWickedFilter, WickedEvent

def linkcache(func):
    def cache(wfilter, chunk, normalized):
        # cache depends on query and match
        # this could use some untangling
        # generic function?
        value = wfilter.cache.get(normalized)
        if not value or '/'.join(wfilter.context.getPhysicalPath()) != wfilter.cache.cache_store.id:
            value = func(wfilter, chunk, normalized)
            if value:
                uid = value[0]['uid']
                wfilter.cache.set((normalized, uid), value)
        return value
    return cache

def getWicked(field, instance, event=None):
    if not event:
        event = WickedEvent()
    return getMultiAdapter((field, instance, event), IWickedFilter)


def match(query):
    def match(self, best_match=True):
        data = query(self)
        if data and best_match:
            return [getMatch(self.chunk, data, normalled=self.normalled)]
        return data
    return match


def cleanUID(brain):
    """takes a brain, returns a hashable value"""
    from Missing import Value
    uid = brain.UID
    if uid is Value:
        uid = brain.data_record_id_
    return uid


def packBrain(brain):
    """
    converts dataobjects in to template ready dictionaries

    >>> from Missing import Value
    >>> class brain(object):
    ...     def getPath(self):
    ...         return '/path'
    ...     data_record_id_=123
    ...     UID='unique'
    ...     getIcon='/donkey.gif'
    >>> packBrain(brain())['uid']
    'unique'

    packBrain needs to filter out Missing.Value that make creep in.

    >>> fbrain = brain()
    >>> brain.UID=Value
    >>> packBrain(fbrain)['uid']
    123
    """
    # missing values are not hashable nor can they be dict keys.  they
    # should never see the light of day. In the rare case that the UID
    # index is updated for an object, substitute the record id

    uid = cleanUID(brain)

    return dict(path=brain.getPath(),
                icon=brain.getIcon,
                uid=uid,
                rid=brain.data_record_id_)


def getMatch(chunk, brains, normalled=None):
    """
    Given a set of query results and the wicked link text, return
    the single brain that represents the correct object to link to, or
    None.

    Assumes that brains are already ordered oldest to newest, so
    the first absolute match is the one returned.  Matches on id
    take priority over matches on title

    all strings are normalized and interned for comparison matches.

    >>> from testing.general import pdo
    >>> mkbrain = lambda i: pdo(getId='-'.join([str(x) for x in i]), Title='%s %s' %i, created=i[1])
    >>> seed = zip('abc', range(3))
    >>> brains = [mkbrain(i) for i in seed]
    >>> chunk = ''
    >>> normalled = ''

    Test null conditions

    >>> getMatch(chunk, brains)
    >>> getMatch(chunk, brains, normalled)
    >>> getMatch(chunk, brains[:1], normalled)

    Test single brain matches

    >>> getMatch('', brains[:1], 'a-0').getId
    'a-0'

    >>> getMatch(brains[0].getId, brains[:1], 'blah').getId
    'a-0'

    >>> getMatch(brains[0].Title, brains[:1]).getId
    'a-0'

    Test multi brain matches. brain 0 should win over brain 3
    for all matches

    >>> from copy import copy
    >>> newbrain = copy(brains[0])
    >>> newbrain.update(dict(created=3))
    >>> brains =   brains + [newbrain]
    >>> getMatch('', brains, 'a-0').created
    0

    >>> getMatch(brains[0].getId, brains).created
    0

    >>> getMatch(brains[0].Title, brains).created
    0

    Test title to chunk match

    >>> brains[3].Title='A unique title'
    >>> getMatch(brains[3].Title, brains).Title
    'A unique title'
    """
    normalled_chunk = normalled
    if not normalled_chunk:
        normalled_chunk = normalize(chunk)
    if not isinstance(brains, list):
        # make a copy to AdvancedQuery sequencing issues
        brains = [x for x in brains]

    # inspect single return case

    if len(brains) == 1 and \
           (brains[0].getId == normalled_chunk \
            or brains[0].getId.strip() == chunk.strip() \
            or normalize(brains[0].Title) == normalled_chunk):
        return brains[0]

    # first, match id

    # reversing the brains into a dict clobbers younger matches with
    # the same id. we'll match against the normalled chunk, then the
    # chunk (for single work chunks)

    btup = [(brain.getId, brain) for brain in brains]
    id_dict = dict(reversed(btup))
    for unk in normalled_chunk, chunk,:
        if id_dict.has_key(unk):
            return id_dict[unk]

    # second, match Title
    brains=[brain for brain in brains \
            if normalize(brain.Title) == normalled_chunk]

    return brains and brains[0] or None



def counter():
    count=0
    while True:
        count+=1
        yield count


_marker = object()
class Memoizer(object):
    propname = '_mp_cache'
    def clearbefore(self, func):
        def clear(*args, **kwargs):
            inst=args[0]
            if hasattr(inst, self.propname):
                delattr(inst, self.propname)
            return func(*args, **kwargs)
        return clear

    def memoizedproperty(self, func):
        return property(self.memoize(func))

    def memoize(self, func):
        def memogetter(*args, **kwargs):
            inst = args[0]
            cache = getattr(inst, self.propname, dict())
            key=hash((func.__name__, args, frozenset(kwargs)))
            val = cache.get(key, _marker)
            if val is _marker:
                val=func(*args, **kwargs)
                cache[key]=val
                setattr(inst, self.propname, cache)
            return val
        return memogetter


_m = Memoizer()
memoize = _m.memoize
memoizedproperty = _m.memoizedproperty
clearbefore = _m.clearbefore


def test_suite():
    import unittest
    from zope.testing import doctest
    optionflags = doctest.REPORT_ONLY_FIRST_FAILURE | doctest.ELLIPSIS
    return doctest.DocTestSuite('wicked.utils',
                                optionflags=optionflags)
