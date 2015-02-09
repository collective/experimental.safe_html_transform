from Acquisition import aq_base
from time import time


def findObjects(origin):
    """ generator to recursively find and yield all zope objects below
        the given start point """
    traverse = origin.unrestrictedTraverse
    base = '/'.join(origin.getPhysicalPath())
    cut = len(base) + 1
    paths = [base]
    for idx, path in enumerate(paths):
        obj = traverse(path)
        yield path[cut:], obj
        if hasattr(aq_base(obj), 'objectIds'):
            for id in obj.objectIds():
                paths.insert(idx + 1, path + '/' + id)


def timer(func=time):
    """ set up a generator returning the elapsed time since the last call """
    def gen(last=func()):
        while True:
            elapsed = func() - last
            last = func()
            yield '%.3fs' % elapsed
    return gen()


def checkpointIterator(function, interval=100):
    """ the iterator will call the given function for every nth invocation """
    counter = 0
    while True:
        counter += 1
        if counter % interval == 0:
            function()
        yield None
