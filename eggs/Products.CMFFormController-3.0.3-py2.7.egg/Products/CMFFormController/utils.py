import logging
import sys
import traceback

logger = logging.getLogger('CMFFormController')

def log(summary='', text='', log_level=logging.INFO):
    logger.log(log_level, '%s \n%s' % (summary, text))

# Enable scripts to get the string value of an exception
# even if the thrown exception is a string and not a
# subclass of Exception.
def exceptionString():
    s = sys.exc_info()[:2]  # don't assign the traceback to s
                            # (otherwise will generate a circular reference)
    if s[0] == None:
        return None
    if isinstance(s[0], basestring):
        return s[0]
    return str(s[1])

# provide a way of dumping an exception to the log even if we
# catch it and otherwise ignore it
def logException():
    """Dump an exception to the log"""
    log(summary=str(exceptionString()),
        text='\n'.join(traceback.format_exception(*sys.exc_info())),
        log_level=logging.WARNING)
