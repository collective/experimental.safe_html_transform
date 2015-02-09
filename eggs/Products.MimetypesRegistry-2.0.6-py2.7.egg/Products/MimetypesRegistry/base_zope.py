"""some common utilities
"""

FB_REGISTRY = None

# base class
from ExtensionClass import Base
from Acquisition import aq_base

# logging function
import logging

logger = logging.getLogger('PortalTransforms')

def log(msg, severity=logging.INFO, id='PortalTransforms'):
    logger.log(severity, msg)

# directory where template for the ZMI are located
import os.path
_www = os.path.join(os.path.dirname(__file__), 'www')

# list and dict classes to use
from Persistence import PersistentMapping as DictClass
try:
    from ZODB.PersistentList import PersistentList as ListClass
except ImportError:
    from persistent.list import PersistentList as ListClass

from zope.interface import Interface, Attribute

def implements(object, interface):
    return interface.providedBy(object)

# getToolByName
from Products.CMFCore.utils import getToolByName as _getToolByName
_marker = []

def getToolByName(context, name, default=_marker):
    global FB_REGISTRY
    tool = _getToolByName(context, name, default)
    if name == 'mimetypes_registry' and tool is default:
        if FB_REGISTRY is None:
            from Products.MimetypesRegistry.MimeTypesRegistry \
                 import MimeTypesRegistry
            FB_REGISTRY = MimeTypesRegistry()
        tool = FB_REGISTRY
    return tool

from zExceptions import BadRequest

__all__ = ('Base', 'log', 'DictClass', 'ListClass', 'getToolByName', 'aq_base',
           'Interface', 'Attribute', 'implements', '_www',
           'BadRequest', )
