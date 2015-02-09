"""some common utilities
"""
import logging
from time import time
from types import UnicodeType, StringType

STRING_TYPES = (UnicodeType, StringType)

class MimeTypeException(Exception):
    pass

# logging function
logger = logging.getLogger('MimetypesRegistry')

def log(msg, severity=logging.INFO, id='MimetypesRegistry'):
    logger.log(severity, msg)

# directory where template for the ZMI are located
import os.path
_www = os.path.join(os.path.dirname(__file__), 'www')

from AccessControl import ModuleSecurityInfo
security = ModuleSecurityInfo()
security.declarePrivate('logging')
security.declarePrivate('os')
security.declarePrivate('time')
