"""Dummies used in ZCML tests
"""

from zope.interface import Interface, implements
from zope import schema

from plone.contentrules.rule.interfaces import IRuleElementData

class ITestCondition(Interface):
    test = schema.TextLine(title=u"Test property")

class TestCondition(object):
    implements(ITestCondition, IRuleElementData)
    test = u""

    summary = u"Test condition"
    element = u"test.condition"

class ITestAction(Interface):
    test = schema.TextLine(title=u"Test property")

class TestAction(object):
    implements(ITestAction, IRuleElementData)
    test = u""

    summary = u"Test action"
    element = u"test.action"
