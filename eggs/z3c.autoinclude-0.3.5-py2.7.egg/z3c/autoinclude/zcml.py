from zope.interface import Interface
from zope.configuration.xmlconfig import include, includeOverrides
from zope.configuration.fields import GlobalObject
from zope.dottedname.resolve import resolve
from zope.schema import BytesLine

from z3c.autoinclude import api
from z3c.autoinclude.dependency import DependencyFinder
from z3c.autoinclude.utils import distributionForPackage
from z3c.autoinclude.plugin import PluginFinder

import logging
log = logging.getLogger("z3c.autoinclude")

def includeZCMLGroup(_context, info, filename, override=False):
    includable_zcml = info[filename]
    # ^^ a key error would mean that we are trying to include a group of ZCML
    #    with a filename that wasn't ever searched for. that *should* be an error

    zcml_context = repr(_context.info)

    for dotted_name in includable_zcml:
        log.debug('including file %s from package %s at %s', filename, dotted_name, zcml_context)

    for dotted_name in includable_zcml:
        includable_package = resolve(dotted_name)
        if override:
            includeOverrides(_context, filename, includable_package)
        else:
            include(_context, filename, includable_package)


class IIncludeDependenciesDirective(Interface):
    """Auto-include any ZCML in the dependencies of this package."""
    
    package = GlobalObject(
        title=u"Package to auto-include for",
        description=u"""
        Auto-include all dependencies of this package.
        """,
        required=True,
        )

def includeDependenciesDirective(_context, package):

    if api.dependencies_disabled():
        log.warn('z3c.autoinclude.dependency is disabled but is being invoked by %s' % _context.info)
        return

    dist = distributionForPackage(package)
    info = DependencyFinder(dist).includableInfo(['configure.zcml', 'meta.zcml'])

    includeZCMLGroup(_context, info, 'meta.zcml')
    includeZCMLGroup(_context, info, 'configure.zcml')

def includeDependenciesOverridesDirective(_context, package):

    if api.dependencies_disabled():
        log.warn('z3c.autoinclude.dependency is disabled but is being invoked by %s' % _context.info)
        return

    dist = distributionForPackage(package)
    info = DependencyFinder(dist).includableInfo(['overrides.zcml'])
    includeZCMLGroup(_context, info, 'overrides.zcml', override=True)


class IIncludePluginsDirective(Interface):
    """Auto-include any ZCML in the dependencies of this package."""
    
    package = GlobalObject(
        title=u"Package to auto-include for",
        description=u"""
        Auto-include all plugins to this package.
        """,
        required=True,
        )

    file = BytesLine(
        title=u"ZCML filename to look for",
        description=u"""
        Name of a particular ZCML file to look for.
        If omitted, autoinclude will scan for standard filenames
        (e.g. meta.zcml, configure.zcml, overrides.zcml)
        """,
        required=False,
        )


def includePluginsDirective(_context, package, file=None):

    if api.plugins_disabled():
        log.warn('z3c.autoinclude.plugin is disabled but is being invoked by %s' % _context.info)
        return

    dotted_name = package.__name__

    if file is None:
        zcml_to_look_for = ['meta.zcml', 'configure.zcml']
    else:
        zcml_to_look_for = [file]
    info = PluginFinder(dotted_name).includableInfo(zcml_to_look_for)

    for filename in zcml_to_look_for:
        includeZCMLGroup(_context, info, filename)

def includePluginsOverridesDirective(_context, package, file=None):

    if api.plugins_disabled():
        log.warn('z3c.autoinclude.plugin is disabled but is being invoked by %s' % _context.info)
        return

    dotted_name = package.__name__
    if file is None:
        zcml_to_look_for = ['overrides.zcml']
    else:
        zcml_to_look_for = [file]
    info = PluginFinder(dotted_name).includableInfo(zcml_to_look_for)

    for filename in zcml_to_look_for:
        includeZCMLGroup(_context, info, filename, override=True)
