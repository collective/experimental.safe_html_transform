##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors>
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Upgrade steps and registry.
"""

from pkg_resources import parse_version

from BTrees.OOBTree import OOBTree

from Products.GenericSetup.interfaces import IUpgradeSteps
from Products.GenericSetup.registry import GlobalRegistryStorage


def normalize_version(version):
    if isinstance(version, tuple):
        version = '.'.join(version)
    if version in (None, 'unknown', 'all'):
        return None
    return parse_version(version)


class UpgradeRegistry(object):
    """Registry of upgrade steps, by profile.

    Registry keys are profile ids.

    Each registry value is a nested mapping:
      - id -> step for single steps
      - id -> [ (id1, step1), (id2, step2) ] for nested steps
    """
    def __init__(self):
        self._registry = GlobalRegistryStorage(IUpgradeSteps)

    def __getitem__(self, key):
        return self._registry.get(key)

    def keys(self):
        return self._registry.keys()

    def clear(self):
        self._registry.clear()

    def getUpgradeStepsForProfile(self, profile_id):
        """Return the upgrade steps mapping for a given profile, or
        None if there are no steps registered for a profile matching
        that id.
        """
        profile_steps = self._registry.get(profile_id)
        if profile_steps is None:
            self._registry[profile_id] = OOBTree()
            profile_steps = self._registry.get(profile_id)
        return profile_steps

    def getUpgradeStep(self, profile_id, step_id):
        """Returns the specified upgrade step for the specified
        profile, or None if it doesn't exist.
        """
        profile_steps = self._registry.get(profile_id)
        if profile_steps is not None:
            step = profile_steps.get(step_id, None)
            if step is None:
                for key in profile_steps.keys():
                    if type(profile_steps[key]) == list:
                        subs = dict(profile_steps[key])
                        step = subs.get(step_id, None)
                        if step is not None:
                            break
            elif type(step) == list:
                subs = dict(step)
                step = subs.get(step_id, None)
            return step

_upgrade_registry = UpgradeRegistry()


class UpgradeEntity(object):
    """
    Base class for actions to be taken during an upgrade process.
    """
    def __init__(self, title, profile, source, dest, desc, checker=None,
                 sortkey=0):
        self.id = str(abs(hash('%s%s%s%s' % (title, source, dest, sortkey))))
        self.title = title
        if source == '*':
            source = None
        elif isinstance(source, basestring):
            source = tuple(source.split('.'))
        self.source = source
        if dest == '*':
            dest = None
        elif isinstance(dest, basestring):
            dest = tuple(dest.split('.'))
        self.dest = dest
        self.description = desc
        self.checker = checker
        self.sortkey = sortkey
        self.profile = profile

    def versionMatch(self, source):
        source = normalize_version(source)
        if source is None:
            return True
        start = normalize_version(self.source)
        stop = normalize_version(self.dest)
        return ((start is None or start == source) and
                (stop is None or stop > source))

    def isProposed(self, tool, source):
        """Check if a step can be applied.

        False means already applied or does not apply.
        True means can be applied.
        """
        checker = self.checker
        if checker is None:
            return self.versionMatch(source)
        return self.versionMatch(source) and checker(tool)


class UpgradeStep(UpgradeEntity):
    """A step to upgrade a component.
    """
    def __init__(self, title, profile, source, dest, desc, handler,
                 checker=None, sortkey=0):
        super(UpgradeStep, self).__init__(title, profile, source, dest,
                                          desc, checker, sortkey)
        self.handler = handler

    def doStep(self, tool):
        self.handler(tool)


class UpgradeDepends(UpgradeEntity):
    """A specialized upgrade step that re-runs a particular import
    step from the profile.
    """
    def __init__(self, title, profile, source, dest, desc, import_profile=None,
                 import_steps=[], run_deps=False, purge=False, checker=None,
                 sortkey=0):
        super(UpgradeDepends, self).__init__(title, profile, source, dest,
                                          desc, checker, sortkey)
        self.import_profile = import_profile
        self.import_steps = import_steps
        self.run_deps = run_deps
        self.purge = purge

    PROFILE_PREFIX = 'profile-%s'

    def doStep(self, tool):
        if self.import_profile is None:
            profile_id = self.PROFILE_PREFIX % self.profile
        else:
            profile_id = self.PROFILE_PREFIX % self.import_profile
        if self.import_steps:
            for step in self.import_steps:
                tool.runImportStepFromProfile(profile_id, step,
                                              run_dependencies=self.run_deps,
                                              purge_old=self.purge)
        else:
            # if no steps are specified we assume we want to reimport
            # the entire profile
            ign_deps = not self.run_deps
            tool.runAllImportStepsFromProfile(profile_id,
                                              purge_old=self.purge,
                                              ignore_dependencies=ign_deps)

def _registerUpgradeStep(step):
    profile_id = step.profile
    profile_steps = _upgrade_registry.getUpgradeStepsForProfile(profile_id)
    profile_steps[step.id] = step

def _registerNestedUpgradeStep(step, outer_id):
    profile_id = step.profile
    profile_steps = _upgrade_registry.getUpgradeStepsForProfile(profile_id)
    nested_steps = profile_steps.get(outer_id, [])
    nested_steps.append((step.id, step))
    profile_steps[outer_id] = nested_steps

def _extractStepInfo(tool, id, step, source):
    """Returns the info data structure for a given step.
    """
    proposed = step.isProposed(tool, source)
    if not proposed:
        source = normalize_version(source)
        if source is not None:
            start = normalize_version(step.source)
            stop = normalize_version(step.dest)
            if ((start is not None and start < source) or
                (stop is not None and stop <= source)):
                return
    info = {
        'id': id,
        'step': step,
        'title': step.title,
        'source': step.source,
        'dest': step.dest,
        'description': step.description,
        'proposed': proposed,
        'sortkey': step.sortkey,
        }
    return info

def listProfilesWithUpgrades():
    return _upgrade_registry.keys()

def listUpgradeSteps(tool, profile_id, source):
    """Lists upgrade steps available from a given version, for a given
    profile id.
    """
    res = []
    profile_steps = _upgrade_registry.getUpgradeStepsForProfile(profile_id)
    for id, step in profile_steps.items():
        if isinstance(step, UpgradeEntity):
            info = _extractStepInfo(tool, id, step, source)
            if info is None:
                continue
            normsrc = normalize_version(step.source)
            res.append(((normsrc or '', step.sortkey, info['proposed']), info))
        else: # nested steps
            nested = []
            outer_proposed = False
            for inner_id, inner_step in step:
                info = _extractStepInfo(tool, inner_id, inner_step, source)
                if info is None:
                    continue
                nested.append(info)
                outer_proposed = outer_proposed or info['proposed']
            if nested:
                src = nested[0]['source']
                sortkey = nested[0]['sortkey']
                normsrc = normalize_version(src)
                res.append(((normsrc or '', sortkey, outer_proposed), nested))
    res.sort()
    res = [i[1] for i in res]
    return res
