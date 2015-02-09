"""Security helpers and layers
"""

from plone.testing import Layer

_checkersStack = []

def pushCheckers():
    """Push the current set of security checkers onto a stack. You should
    normally do this during layer set-up, before loading any ZCML files that
    could load checkers.
    """

    global _checkersStack

    from zope.security import checker

    _checkersStack.append(checker._checkers.copy())

def popCheckers():
    """Pop the most recently pushed set of security checkers from the stack.
    You should normally do this during layer tear-down. You *must* keep calls
    to ``popCheckers()`` balanced with calls to ``pushCheckers()``.
    """

    global _checkersStack

    from zope.security import checker

    checker._checkers = _checkersStack.pop()

class Checkers(Layer):
    """Ensures correct isolation of security checkers in zope.security.
    """

    defaultBases = ()

    def setUp(self):
        pushCheckers()

    def tearDown(self):
        popCheckers()

CHECKERS = Checkers()
