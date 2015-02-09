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
from general import dummy
from wicked.factories import ContentCacheManager

def fakecacheiface(cached):
    def call(*args):
        return args[0]
    def set(*args):
        return "<link cached>"
    methods = dict(__call__=call, set=set)
    cacheman=type('dummy',
                  (dict,), methods)()
    cacheman.update(cached)
    return cacheman

class query(object):

    brains = ['We are brains!']

    def scopedSearch(self):
        if self.chunk != 'dud':
            return self.brains

    def configure(self, chunk, normalized, scope):
        self.chunk = chunk
        self.normalized = normalized
        self.scope = scope

    def search(self):
        if self.chunk != 'dud' and self.chunk != 'scoped':
            return self.brains

def argchug(rets):
    def function(*args, **kwargs):
        return rets

def fakefilter():
    def conf(*args, **kw):
        self = list(args).pop()
        [setattr(self, k, v) for k, v in kw.items()]
        return kw
    conf = classmethod(conf)
    kdict = dict(configure=conf, scope='/scope/')
    wfilter = dummy(kdict, name='wfilter')
    wfilter.query_iface = query()
    wfilter.getMatch = argchug(('uid', 'link'))
    wfilter.resolver = query()
    wfilter.section=hash(wfilter)
    wfilter.cache=ContentCacheManager(dummy(dict()))
    return wfilter
