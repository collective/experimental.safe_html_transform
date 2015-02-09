# -*- coding: utf-8 -*-
from plone.behavior.interfaces import IBehavior
from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.interfaces import IDexterityContent
from plone.dexterity.interfaces import IDexterityFTI
from zope.component import adapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.interface import implementer


@implementer(IBehaviorAssignable)
@adapter(IDexterityContent)
class DexterityBehaviorAssignable(object):
    """Support plone.behavior behaviors stored in the FTI
    """

    def __init__(self, context):
        self.fti = getUtility(IDexterityFTI, name=context.portal_type)

    def supports(self, behavior_interface):
        for behavior in self.enumerateBehaviors():
            if behavior_interface in behavior.interface._implied:
                return True
        return False

    def enumerateBehaviors(self):
        for name in self.fti.behaviors:
            behavior = queryUtility(IBehavior, name=name)
            if behavior is not None:
                yield behavior
