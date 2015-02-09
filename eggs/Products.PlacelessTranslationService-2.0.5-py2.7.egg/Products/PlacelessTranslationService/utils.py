from UserDict import UserDict
import sys, os

import logging
logger = logging.getLogger('PlacelessTranslationService')

import zope.deprecation


class Registry(UserDict):

    def register(self, name, value):
        self[name] = value


def log(msg, severity=logging.DEBUG, detail='', error=None):
    if isinstance(msg, unicode):
        msg = msg.encode(sys.getdefaultencoding(), 'replace')
    if isinstance(detail, unicode):
        detail = detail.encode(sys.getdefaultencoding(), 'replace')
    logger.log(severity, '%s \n%s', msg, detail)


def make_relative_location(popath):
    # return ("INSTANCE_HOME", stripped po path)
    # when po is located below INSTANCE_HOME
    # and return ("ZOPE_HOME", stripped po path)
    # when po is located below ZOPE_HOME

    popath = os.path.normpath(popath)
    instance_home = os.path.normpath(INSTANCE_HOME) + os.sep
    zope_home = os.path.normpath(ZOPE_HOME) + os.sep

    if popath.startswith(instance_home):
        return ("INSTANCE_HOME", popath[len(instance_home):])
    elif popath.startswith(zope_home):
        return ("ZOPE_HOME", popath[len(zope_home):])
    else:
        return ("ABSOLUTE", popath)


zope.deprecation.deprecated(
   ('Registry', 'make_relative_location'),
    "PlacelessTranslationService.utils Registry and make_relative_location "
    "are deprecated and will be removed in the next major version of PTS."
   )
