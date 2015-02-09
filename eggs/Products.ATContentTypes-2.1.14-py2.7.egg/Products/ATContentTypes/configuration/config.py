import os

from ZConfig.loader import ConfigLoader
from Globals import INSTANCE_HOME
from Products.ATContentTypes.configuration.schema import atctSchema

# directories
INSTANCE_ETC = os.path.join(INSTANCE_HOME, 'etc')
_here = os.path.dirname(__file__)
ATCT_HOME = os.path.dirname(os.path.abspath(os.path.join(_here)))
ATCT_ETC = os.path.join(ATCT_HOME, 'etc')

# files
CONFIG_NAME = 'atcontenttypes.conf'
INSTANCE_CONFIG = os.path.join(INSTANCE_ETC, CONFIG_NAME)
ATCT_CONFIG = os.path.join(ATCT_ETC, CONFIG_NAME)
ATCT_CONFIG_IN = os.path.join(ATCT_ETC, CONFIG_NAME + '.in')

# check files for existence
if not os.path.isfile(INSTANCE_CONFIG):
    INSTANCE_CONFIG = None
if not os.path.isfile(ATCT_CONFIG):
    ATCT_CONFIG = None
if not os.path.isfile(ATCT_CONFIG_IN):
    raise RuntimeError("Unable to find configuration file at %s" %
                        ATCT_CONFIG_IN)
FILES = (INSTANCE_CONFIG, ATCT_CONFIG, ATCT_CONFIG_IN,)

# config
zconf, handler, conf_file = None, None, None


def loadConfig(files, schema=atctSchema, overwrite=False):
    """Config loader

    The config loader tries to load the first existing file
    """
    global zconf, handler, conf_file
    if not isinstance(files, (tuple, list)):
        files = (files, )
    if zconf is not None and not overwrite:
        raise RuntimeError, 'Configuration is already loaded'
    for file in files:
        if file is not None:
            if not os.path.exists(file):
                raise RuntimeError, '%s does not exist' % file
            conf_file = file
            zconf, handler = ConfigLoader(schema).loadURL(conf_file)
            break


loadConfig(FILES)

__all__ = ('zconf', 'handler', 'conf_file')
