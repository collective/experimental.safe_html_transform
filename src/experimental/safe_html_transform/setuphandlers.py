# -*- coding: utf-8 -*-
from zope.component import getUtility
from Products.PortalTransforms.interfaces import IPortalTransformsTool


def isNotCurrentProfile(context):
    return context.readDataFile('experimentalsafehtmltransform_marker.txt') is None


def post_install(context):
    """Post install script"""
    if isNotCurrentProfile(context):
        return
    # Do something during the installation of this package


def unregister_transform(context, transform):
    transform_tool = getUtility(IPortalTransformsTool)
    if hasattr(transform_tool, transform):
        transform_tool.unregisterTransform(transform)
