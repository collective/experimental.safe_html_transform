from zope.interface import Interface
from zope.schema import TextLine

test_log = []

def clear_test_log():
    while test_log:
        test_log.pop()

class ITestDirective(Interface):
    """Auto-include any ZCML in the dependencies of this package."""
    
    test_string = TextLine(
        title=u"Test package string",
        description=u"""
        Append a value to a global variable to inspect later
        """,
        required=True,
        )

def testDirective(_context, test_string):
    test_log.append(test_string)
