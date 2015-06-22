# -*- coding: utf-8 -*-
import logging
from zope.component import getUtility
from Products.PortalTransforms.interfaces import IPortalTransformsTool
from Products.CMFCore.utils import getToolByName


def isNotCurrentProfile(context):
    return context.readDataFile('experimentalsafehtmltransform_marker.txt') is None


def post_install(context):
    """Post install script"""
    if isNotCurrentProfile(context):
        return
    # Do something during the installation of this package
    unregister_transform(context, 'safe_html')


def unregister_transform(context, transform):
    transform_tool = getUtility(IPortalTransformsTool)
    if hasattr(transform_tool, transform):
        transform_tool.unregisterTransform(transform)


def installTransform(context, logger=None):
    if logger is None:
        logger = logging.getLogger('experimental.safe_html_transform')
    if hasattr(context, 'readDataFile'):
        if isNotCurrentProfile(context):
            return
    else:
        pass
    transforms = getToolByName(context, 'portal_transforms')
    transforms.unregisterTransform('safe_html')
    transforms.manage_addTransform('safe_html', 'experimental.safe_html_transform.%s' % 'safe_html')
