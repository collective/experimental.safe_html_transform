import sys
_marker = object()

class ResourceManager(object):
    """Mixin class for resource managers.
    """

    __bases__ = () # must be set as an instance variable by subclass

    def __init__(self):
        self._resources = {}
        self.baseResolutionOrder = tuple(self._resourceResolutionOrder(self))

    def get(self, key, default=None):
        for resourceManager in self.baseResolutionOrder:
            if key in getattr(resourceManager, '_resources', {}):
                # Get the value on the top of the stack
                return resourceManager._resources[key][-1][0]
        return default

    # Dict API

    def __getitem__(self, key):
        item = self.get(key, _marker)
        if item is _marker:
            raise KeyError(key)
        return item

    def __contains__(self, key):
        return self.get(key, _marker) is not _marker

    def __setitem__(self, key, value):
        foundStack = False

        for resourceManager in self.baseResolutionOrder:
            if key in getattr(resourceManager, '_resources', {}):
                stack = resourceManager._resources[key]
                foundStack = True

                foundStackItem = False
                for idx in range(len(stack)-1, -1, -1):
                    if stack[idx][1] is self:

                        # This layer instance has already added an item to
                        # the stack. Update that item instead of pushing a new
                        # item onto the stack.
                        stack[idx][0] = value

                        foundStackItem = True
                        break

                # This layer instance does not have a stack item yet. Create
                # a new one.
                if not foundStackItem:
                    stack.append([value, self,])

                # Note: We do not break here on purpose: it's possible
                # that there is resource stack in another branch of the base
                # tree; we keep those in sync.

        # This resource is not shadowing any other: create a new stack here
        if not foundStack:
            self._resources[key] = [[value, self]]

    def __delitem__(self, key):
        found = False
        for resourceManager in self.baseResolutionOrder:
            if key in getattr(resourceManager, '_resources', {}):
                stack = resourceManager._resources[key]
                for idx in range(len(stack)-1, -1, -1):
                    if stack[idx][1] is self:
                        del stack[idx]

                        if len(stack) == 0:
                            del resourceManager._resources[key]

                        found = True

                # Note: We do not break here on purpose: it's possible
                # that there is another stack in another branch of the base
                # tree; we keep those in sync.

        if not found:
            raise KeyError(key)

    # Helpers

    # This is basically the Python MRO algorithm, adapted from
    # http://www.python.org/download/releases/2.3/mro/

    def _mergeResourceManagers(self, seqs):

        res = []
        i = 0

        while True:
            nonemptyseqs = [seq for seq in seqs if seq]

            if not nonemptyseqs:
                return res

            i += 1

            for seq in nonemptyseqs: # find merge candidates among seq heads
                cand = seq[0]
                nothead=[s for s in nonemptyseqs if cand in s[1:]]
                if nothead:
                    cand=None #reject candidate
                else:
                    break

            if not cand:
                raise TypeError(u"Inconsistent layer hierarchy!")

            res.append(cand)
            for seq in nonemptyseqs: # remove cand
                if seq[0] == cand:
                    del seq[0]

    def _resourceResolutionOrder(self, instance):
        return self._mergeResourceManagers(
                [ [instance] ] +
                map(self._resourceResolutionOrder, instance.__bases__) +
                [ list(instance.__bases__) ]
            )

class Layer(ResourceManager):
    """A base class for layers.
    """

    # Set this at the class level to a tuple of layer *instances* to treat
    # as bases for this layer. This may be overridden by passing a tuple
    # to the Layer constructor.

    defaultBases = ()

    def __init__(self, bases=None, name=None, module=None):
        """Create an instance of the layer. Normally this is done once, at
        module scope.

        Pass a tuple of bases to override the default set of bases.

        Pass a name to override the layer name. By default, it is the
        name of the layer class. NOTE: Each layer requires a unique name,
        so if you instantiate the layer class more than once, you need to
        supply a new, unique name. As a precaution, the name is required
        if bases is given.

        Pass a module to override the layer module. By default, it is the
        module of the layer class.
        """

        if self.__class__ is Layer and name is None:
            raise ValueError('The `name` argument is required when instantiating `Layer` directly')

        if name is None and bases is not None:
            raise ValueError('The `name`` argument is required when overriding bases with the `bases` argument')

        super(Layer, self).__init__()

        if bases is None:
            bases = self.defaultBases

        try:
            self.__bases__ = tuple(bases)
        except (KeyError, TypeError,):
            raise ValueError('The `bases` argument must be a sequence.')

        if name is None:
            name = self.__class__.__name__
        self.__name__ = name

        if module is None:

            # Get the module name of whatever instantiated the layer, not
            # the class, by default

            try:
                module = sys._getframe(1).f_globals['__name__']
            except (ValueError, AttributeError, KeyError,):
                module = self.__class__.__module__

        self.__module__ = module

        super(Layer, self).__init__()

    def __repr__(self):
        return "<Layer '%s.%s'>" % (self.__module__, self.__name__,)

    # Layer lifecycle methods - overriden by subclasses

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSetUp(self):
        pass

    def testTearDown(self):
        pass

def layered(suite, layer, addLayerToDoctestGlobs=True):
    """Add the given layer to the given suite and return the suite.

    If ``addLayerToDoctestGlobs`` is ``True``, the layer will be added to the
    globs (global namespace) of any doctests in the suite, under the name
    ``layer``, provided no such glob exists already.
    """
    suite.layer = layer

    if addLayerToDoctestGlobs:
        for test in suite:
            if hasattr(test, '_dt_test'):
                globs = test._dt_test.globs
                if not 'layer' in globs:
                    globs['layer'] = layer

    return suite
