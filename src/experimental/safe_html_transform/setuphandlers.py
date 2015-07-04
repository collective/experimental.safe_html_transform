# -*- coding: utf-8 -*-
import pkgutil
import logging
from Products.CMFCore.utils import getToolByName
import experimental.safe_html_transform.transforms


def isNotCurrentProfile(context):
    return context.readDataFile('experimentalsafehtmltransform_marker.txt') is None


def post_install(context):
    """Post install script"""
    if isNotCurrentProfile(context):
        return
    # Do something during the installation of this package
    uninstallOldTransform(context)
    installNewTransform(context)


def availableTransforms():
    try:
        return [x[1] for x
                in pkgutil.iter_modules(experimental.safe_html_transform.transforms.__path__)
                if x[1] != 'mimetypes']
    except ImportError:
        return []


def uninstallOldTransform(context, logger=None):
    if logger is None:
        logger = logging.getLogger('experimental.safe_html_transform')
    pt = getToolByName(context, 'portal_transforms')
    # get name of safe_html transform from our add-on.
    transforms = 'safe_html'
    # check for our transform name in the portal_tranform
    if transforms in pt:
        pt.unregisterTransform(transforms)
        logger.info('Unregistered %s' % transforms)


def installNewTransform(context, logger=None):
    if logger is None:
        logger = logging.getLogger('experimental.safe_html_transform')
    transforms = getToolByName(context, 'portal_transforms')
    for tform in availableTransforms():
        transforms.manage_addTransform(tform, 'experimental.safe_html_transform.transforms.%s' % tform)
        logger.info('Registered %s' % tform)
