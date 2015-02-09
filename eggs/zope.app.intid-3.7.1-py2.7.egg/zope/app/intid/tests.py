import unittest
from zope.testing import doctest

def test_imports():
    """
    All core functionality was moved to zope.intid, so the tests are
    moved as well. Here, we only test that backward-compatibility imports
    are still working.

    >>> from zope.app.intid import IntIds, intIdEventNotify
    >>> from zope.app.intid import addIntIdSubscriber, removeIntIdSubscriber
    >>> IntIds
    <class 'zope.intid.IntIds'>
    >>> intIdEventNotify
    <function intIdEventNotify at 0x...>
    >>> addIntIdSubscriber
    <function addIntIdSubscriber at 0x...>
    >>> removeIntIdSubscriber
    <function removeIntIdSubscriber at 0x...>

    >>> from zope.app.intid.interfaces import (
    ...     IIntIdsQuery,
    ...     IIntIdsSet,
    ...     IIntIdsManage,
    ...     IIntIds,
    ...     IIntIdEvent,
    ...     IIntIdAddedEvent,
    ...     IIntIdRemovedEvent,
    ...     IntIdAddedEvent,
    ...     IntIdRemovedEvent
    ... )
    >>> IIntIdsQuery
    <InterfaceClass zope.intid.interfaces.IIntIdsQuery>
    >>> IIntIdsSet
    <InterfaceClass zope.intid.interfaces.IIntIdsSet>
    >>> IIntIdsManage
    <InterfaceClass zope.intid.interfaces.IIntIdsManage>
    >>> IIntIds
    <InterfaceClass zope.intid.interfaces.IIntIds>
    >>> IIntIdEvent
    <InterfaceClass zope.intid.interfaces.IIntIdEvent>
    >>> IIntIdAddedEvent
    <InterfaceClass zope.intid.interfaces.IIntIdAddedEvent>
    >>> IIntIdRemovedEvent
    <InterfaceClass zope.intid.interfaces.IIntIdRemovedEvent>
    >>> IntIdAddedEvent
    <class 'zope.intid.interfaces.IntIdAddedEvent'>
    >>> IntIdRemovedEvent
    <class 'zope.intid.interfaces.IntIdRemovedEvent'>
    """

def test_suite():
    return unittest.TestSuite((
        doctest.DocTestSuite(optionflags=doctest.ELLIPSIS),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
