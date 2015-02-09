===================
 forever decorators
===================

These remember a value "forever", i.e. until the process is restarted. They
work on both global functions and class functions.

    >>> from plone.memoize import forever
    
    >>> @forever.memoize
    ... def remember(arg1, arg2):
    ...     print "Calculating"
    ...     return arg1 + arg2
    
No matter how many times we call this function with a particular set of
arguments, it will only perform its calculation once.
    
    >>> remember(1, 1)
    Calculating
    2
    >>> remember(1, 1)
    2
    >>> remember(1, 2)
    Calculating
    3
    >>> remember(1, 2)
    3
    
This also works for methods in classes.
    
    >>> class Test(object):
    ...     
    ...     @forever.memoize
    ...     def remember(self, arg1, arg2):
    ...         print "Calculating"
    ...         return arg1 + arg2
    
    >>> t = Test()
    >>> t.remember(1, 1)
    Calculating
    2
    >>> t.remember(1, 1)
    2
    >>> t.remember(1, 2)
    Calculating
    3
    >>> t.remember(1, 2)
    3
