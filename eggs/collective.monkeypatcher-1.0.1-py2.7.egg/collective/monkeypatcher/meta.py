# -*- coding: utf-8 -*-
# $Id: meta.py 146856 2010-10-23 21:36:39Z hannosch $
"""ZCML handling, and applying patch"""

import re
import pkg_resources
import logging

from zope.interface import Interface, implements
from zope.configuration.fields import GlobalObject, PythonIdentifier
from zope.configuration.exceptions import ConfigurationError
from zope.schema import Int, Bool, Text
from zope.event import notify

import interfaces

log = logging.getLogger('collective.monkeypatcher')

class IMonkeyPatchDirective(Interface):
    """ZCML directive to apply a monkey patch late in the configuration cycle.
    This version replaces one object with another.
    """

    class_ = GlobalObject(title=u"The class being patched", required=False)
    module = GlobalObject(title=u"The module being patched", required=False)
    handler = GlobalObject(title=u"A function to perform the patching.",
                           description=u"Must take three parameters: class/module, original (string), and replacement",
                           required=False)
    original = PythonIdentifier(title=u"Method or function to replace")
    replacement = GlobalObject(title=u"Method to function to replace with")
    preservedoc = Bool(title=u"Preserve docstrings?", required=False, default=True)
    preserveOriginal = Bool(title=u'Preserve the original function so that it is reachable view prefix _old_. Only works for def handler.',
                            default=False, required=False)
    preconditions = Text(title=u'Preconditions (multiple, separated by space) to be satisified before applying this patch. Example: Products.LinguaPlone<=1.4.3',
                            required=False, default=u'')
    ignoreOriginal = Bool(title=u"Ignore if the orginal function isn't present on the class/module being patched",
                          default=False)
    docstringWarning = Bool(title=u"Add monkey patch warning in docstring", required=False, default=True)
    description = Text(title=u'Some comments about your monkey patch', required=False, default=u"(No comment)")
    order = Int(title=u"Execution order", required=False, default=1000)


def replace(_context, original, replacement, class_=None, module=None, handler=None, preservedoc=True,
            docstringWarning=True, description=u"(No comment)", order=1000, ignoreOriginal=False, 
            preserveOriginal=False, preconditions=u''):
    """ZCML directive handler"""

    if class_ is None and module is None:
        raise ConfigurationError(u"You must specify 'class' or 'module'")
    if class_ is not None and module is not None:
        raise ConfigurationError(u"You must specify one of 'class' or 'module', but not both.")

    scope = class_ or module

    to_be_replaced = getattr(scope, original, None)

    if to_be_replaced is None and not ignoreOriginal:
        raise ConfigurationError("Original %s in %s not found" % (original, str(scope)))

    if preservedoc:
        try:
            replacement.__doc__ = to_be_replaced.__doc__
        except AttributeError:
            pass

    if docstringWarning:
        try:
            patch_warning = "\n**Monkey patched by** '%s.%s'" % (replacement.__module__, replacement.__name__)
            if replacement.__doc__ is None:
                replacement.__doc__ = ''
            replacement.__doc__ += patch_warning
        except AttributeError:
            pass

    # check version
    if preconditions != u'':
        if not _preconditions_matching(preconditions):
            log.info('Preconditions for patching scope %s not met (%s)!' % (scope, preconditions))
            return # fail silently

    if handler is None:
        handler = _default_patch

        if preserveOriginal is True:
            handler = _default_preserve_handler

    _context.action(
        discriminator = None,
        callable = _do_patch,
        order=order,
        args = (handler, scope, original, replacement, repr(_context.info), description))
    return

def _preconditions_matching(preconditions):
    """ Returns True if preconditions matching """

    matcher_r = re.compile(r'^(.*?)([-+!=]+)(.*)$', re.DOTALL | re.IGNORECASE | re.MULTILINE)
    version_r = re.compile(r'^([0-9]+)\.([0-9]+)\.?([0-9]?).*$', re.IGNORECASE | re.MULTILINE)
    ev = pkg_resources.Environment()

    # split all preconds
    for precond in preconditions.split():
        _p = precond.strip()
        package, op, version = matcher_r.search(_p).groups()

        # first try to get package - if not found fail silently
        dp = ev[package.strip()]
        if not dp:
            return True

        # fill versions - we assume having s/th like
        # 1.2.3a2 or 1.2a1 or 1.2.0 - look at regexp
        p_v = map(int, filter(lambda x:x and int(x) or 0, version_r.search(version).groups()))
        p_i = map(int, filter(lambda y:y and int(y) or 0, version_r.search(dp[0].version).groups()))

        if not p_v or not p_i:
            log.error('Could not patch because version not recognized. Wanted: %s, Installed: %s' % (p_v, p_i))
            return False

        # compare operators - dumb if check - could be better
        if op == '-=': return p_v >= p_i
        if op == '+=': return p_v <= p_i
        if op == '!=': return p_v != p_i
        if op in ['=', '==']: return p_v == p_i

        raise Exception, 'Unknown operator %s' % op

class MonkeyPatchEvent(object):
    """Envent raised when a monkeypatch is applied
    see interfaces.IMonkeyPatchEvent
    """

    implements(interfaces.IMonkeyPatchEvent)

    def __init__(self, mp_info):
        self.patch_info = mp_info
        return


def _do_patch(handler, scope, original, replacement, zcml_info, description):
    """Apply the monkey patch through preferred method"""
    
    try:
        org_dotted_name = '%s.%s.%s' % (scope.__module__, scope.__name__, original)
    except AttributeError, e:
        org_dotted_name = '%s.%s' % (scope.__name__, original)

    try:
        new_dotted_name = "%s.%s" % (replacement.__module__, replacement.__name__)
    except AttributeError, e:
        new_dotted_name = "a custom handler: %s" % handler

    log.debug("Monkey patching %s with %s" % (org_dotted_name, new_dotted_name,))

    info = {
        'description': description,
        'zcml_info': zcml_info,
        'original': org_dotted_name,
        'replacement': '%s.%s' % (replacement.__module__, replacement.__name__)}

    notify(MonkeyPatchEvent(info))
    handler(scope, original, replacement)
    return


def _default_patch(scope, original, replacement):
    """Default patch method"""

    setattr(scope, original, replacement)
    return

def _default_preserve_handler(scope, original, replacement):
    """ Default handler that preserves original method """

    OLD_NAME = '_old_%s' % original 

    if not hasattr(scope, OLD_NAME):
        setattr(scope, OLD_NAME, getattr(scope, original))

    setattr(scope, original, replacement)
    return

