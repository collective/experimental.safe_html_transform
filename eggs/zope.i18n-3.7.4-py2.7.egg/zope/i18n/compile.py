import logging
import os
from os.path import join
from stat import ST_MTIME

HAS_PYTHON_GETTEXT = True
try:
    from pythongettext.msgfmt import Msgfmt
    from pythongettext.msgfmt import PoSyntaxError
except ImportError:
    HAS_PYTHON_GETTEXT = False

logger = logging.getLogger('zope.i18n')


def compile_mo_file(domain, lc_messages_path):
    """Creates or updates a mo file in the locales folder."""
    if not HAS_PYTHON_GETTEXT:
        logger.critical("Unable to compile messages: Python `gettext` library missing.")
        return

    base = join(lc_messages_path, domain)
    pofile = str(base + '.po')
    mofile = str(base + '.mo')

    po_mtime = 0
    try:
        po_mtime = os.stat(pofile)[ST_MTIME]
    except (IOError, OSError):
        return

    mo_mtime = 0
    if os.path.exists(mofile):
        # Update mo file?
        try:
            mo_mtime = os.stat(mofile)[ST_MTIME]
        except (IOError, OSError):
            return

    if po_mtime > mo_mtime:
        try:
            mo = Msgfmt(pofile, domain).getAsFile()
            fd = open(mofile, 'wb')
            fd.write(mo.read())
            fd.close()
        except (IOError, OSError, PoSyntaxError):
            logger.warn('Error while compiling %s' % pofile)
