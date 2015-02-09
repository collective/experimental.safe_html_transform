"""Hook the logger.error call."""

import sys
import re
import logging
try:
    from ipdb import set_trace
    from ipdb import post_mortem
except:
    from pdb import set_trace
    from pdb import post_mortem

logger = logging.getLogger('Products.PDBDebugMode')

LoggerClass = logging.getLoggerClass()
orig_error = LoggerClass.error

ignore_matchers = (
    # There's a known error in ZCatalog where deleting a container
    # will generate these log errors for its children
    re.compile(
        '^uncatalogObject unsuccessfully attempted to uncatalog an '
        'object with a uid of ').search,
    # Ignore broken GenericSetup handlers
    re.compile(
        '^Step .* has an invalid import handler$').search,
    re.compile(
        '^Step .* has an invalid export handler$').search,
    )

def error(self, msg, *args, **kw):
    """Drop into pdb when logging an error."""
    result = orig_error(self, msg, *args, **kw)

    if not isinstance(msg, basestring):
        msg = str(msg)

    for matcher in ignore_matchers:
        try:
            match = matcher(msg)
        except:
            logger.exception('Matcher %r failed for log message %r' %
                             (matcher, msg))
        else:
            if match:
                break
    else:
        if kw.get('exc_info'):
            type, value, traceback = sys.exc_info()
            post_mortem(traceback)
        else:
            set_trace()
        
    return result
