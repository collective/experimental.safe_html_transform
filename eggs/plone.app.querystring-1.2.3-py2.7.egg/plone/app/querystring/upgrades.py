# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getUtility
from plone.registry.interfaces import IRegistry


def upgrade_1_to_2_typo_in_registry(context):
    registry = getUtility(IRegistry)
    name = 'plone.app.querystring.field.getObjPositionInParent.operations'
    wrong_value = 'plone.app.querystring.operation.int.greaterThan'
    right_value = 'plone.app.querystring.operation.int.largerThan'
    values = registry.get(name)
    if not values:
        return
    if wrong_value in values:
        del values[values.index(wrong_value)]
    if right_value not in values:
        values.append(right_value)
    registry[name] = values
