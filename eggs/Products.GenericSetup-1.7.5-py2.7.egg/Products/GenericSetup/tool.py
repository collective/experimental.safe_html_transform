##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Classes:  SetupTool
"""

import logging
import os
import time
from cgi import escape
from operator import itemgetter

from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass
from OFS.Folder import Folder
from OFS.Image import File
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from zope import event
from zope.interface import implements

from Products.GenericSetup.context import DirectoryImportContext
from Products.GenericSetup.context import SnapshotExportContext
from Products.GenericSetup.context import SnapshotImportContext
from Products.GenericSetup.context import TarballExportContext
from Products.GenericSetup.context import TarballImportContext
from Products.GenericSetup.differ import ConfigDiff
from Products.GenericSetup.events import BeforeProfileImportEvent
from Products.GenericSetup.events import ProfileImportedEvent
from Products.GenericSetup.interfaces import BASE
from Products.GenericSetup.interfaces import EXTENSION
from Products.GenericSetup.interfaces import ISetupTool
from Products.GenericSetup.interfaces import SKIPPED_FILES
from Products.GenericSetup.permissions import ManagePortal
from Products.GenericSetup.registry import ExportStepRegistry
from Products.GenericSetup.registry import ImportStepRegistry
from Products.GenericSetup.registry import ToolsetRegistry
from Products.GenericSetup.registry import _export_step_registry
from Products.GenericSetup.registry import _import_step_registry
from Products.GenericSetup.registry import _profile_registry
from Products.GenericSetup.upgrade import _upgrade_registry
from Products.GenericSetup.upgrade import listProfilesWithUpgrades
from Products.GenericSetup.upgrade import listUpgradeSteps
from Products.GenericSetup.utils import _computeTopologicalSort
from Products.GenericSetup.utils import _getProductPath
from Products.GenericSetup.utils import _resolveDottedName
from Products.GenericSetup.utils import _wwwdir

IMPORT_STEPS_XML = 'import_steps.xml'
EXPORT_STEPS_XML = 'export_steps.xml'
TOOLSET_XML = 'toolset.xml'

generic_logger = logging.getLogger(__name__)

def exportStepRegistries(context):
    """ Built-in handler for exporting import / export step registries.
    """
    setup_tool = context.getSetupTool()
    logger = context.getLogger('registries')

    import_step_registry = setup_tool.getImportStepRegistry()
    if len(import_step_registry.listSteps()) > 0:
        import_steps_xml = import_step_registry.generateXML()
        context.writeDataFile('import_steps.xml', import_steps_xml, 'text/xml')
        logger.info('Local import steps exported.')
    else:
        logger.debug('No local import steps.')

    export_step_registry = setup_tool.getExportStepRegistry()
    if len(export_step_registry.listSteps()) > 0:
        export_steps_xml = export_step_registry.generateXML()
        context.writeDataFile('export_steps.xml', export_steps_xml, 'text/xml')
        logger.info('Local export steps exported.')
    else:
        logger.debug('No local export steps.')

def importToolset(context):
    """ Import required / forbidden tools from XML file.
    """
    site = context.getSite()
    encoding = context.getEncoding()
    logger = context.getLogger('toolset')

    xml = context.readDataFile(TOOLSET_XML)
    if xml is None:
        logger.debug('Nothing to import.')
        return

    setup_tool = context.getSetupTool()
    toolset = setup_tool.getToolsetRegistry()

    toolset.parseXML(xml, encoding)

    existing_ids = site.objectIds()

    for tool_id in toolset.listForbiddenTools():

        if tool_id in existing_ids:
            site._delObject(tool_id)

    for info in toolset.listRequiredToolInfo():

        tool_id = str(info['id'])
        tool_class = _resolveDottedName(info['class'])
        if tool_class is None:
            logger.warning("Not creating required tool %(id)s, because "
                           "class %(class)s is not found." % info)
            continue

        existing = getattr(aq_base(site), tool_id, None)
        # Don't even initialize the tool again, if it already exists.
        if existing is None:
            try:
                new_tool = tool_class()
            except TypeError:
                new_tool = tool_class(tool_id)
            else:
                new_tool._setId(tool_id)

            site._setObject(tool_id, new_tool)
        else:
            if tool_class is None:
                continue
            unwrapped = aq_base(existing)
            # don't use isinstance here as a subclass may need removing
            if type(unwrapped) != tool_class:
                site._delObject(tool_id)
                site._setObject(tool_id, tool_class())

    logger.info('Toolset imported.')

def exportToolset(context):
    """ Export required / forbidden tools to XML file.
    """
    setup_tool = context.getSetupTool()
    toolset = setup_tool.getToolsetRegistry()
    logger = context.getLogger('toolset')

    xml = toolset.generateXML()
    context.writeDataFile(TOOLSET_XML, xml, 'text/xml')

    logger.info('Toolset exported.')


class SetupTool(Folder):

    """ Profile-based site configuration manager.
    """

    implements(ISetupTool)

    meta_type = 'Generic Setup Tool'

    _baseline_context_id = ''

    _profile_upgrade_versions = {}

    _exclude_global_steps = False

    security = ClassSecurityInfo()

    def __init__(self, id):
        self.id = str(id)
        self._import_registry = ImportStepRegistry()
        self._export_registry = ExportStepRegistry()
        self._toolset_registry = ToolsetRegistry()

    #
    #   ISetupTool API
    #
    security.declareProtected(ManagePortal, 'getEncoding')
    def getEncoding(self):
        """ See ISetupTool.
        """
        return 'utf-8'

    security.declareProtected(ManagePortal, 'getBaselineContextID')
    def getBaselineContextID(self):
        """ See ISetupTool.
        """
        return self._baseline_context_id

    security.declareProtected(ManagePortal, 'setBaselineContext')
    def setBaselineContext(self, context_id, encoding=None):
        """ See ISetupTool.
        """
        self._baseline_context_id = context_id
        self.applyContextById(context_id, encoding)

    security.declareProtected(ManagePortal, 'getExcludeGlobalSteps')
    def getExcludeGlobalSteps(self):
        """ See ISetupTool.
        """
        return self._exclude_global_steps

    security.declareProtected(ManagePortal, 'setExcludeGlobalSteps')
    def setExcludeGlobalSteps(self, value):
        """ See ISetupTool.
        """
        self._exclude_global_steps = value

    security.declareProtected(ManagePortal, 'applyContextById')
    def applyContextById(self, context_id, encoding=None):
        context = self._getImportContext(context_id)
        self.applyContext(context, encoding)

    security.declareProtected(ManagePortal, 'applyContext')
    def applyContext(self, context, encoding=None):
        self._updateImportStepsRegistry(context, encoding)
        self._updateExportStepsRegistry(context, encoding)

    security.declareProtected(ManagePortal, 'getImportStepRegistry')
    def getImportStepRegistry(self):
        """ See ISetupTool.
        """
        return self._import_registry

    security.declareProtected(ManagePortal, 'getExportStepRegistry')
    def getExportStepRegistry(self):
        """ See ISetupTool.
        """
        return self._export_registry

    security.declareProtected(ManagePortal, 'getImportStep')
    def getImportStep(self, step, default=None):
        """Simple wrapper to query both the global and local step registry."""
        res = self._import_registry.getStep(step, self)
        if res is self and not self._exclude_global_steps:
            res = _import_step_registry.getStep(step, self)
        if res is not self:
            return res
        return default

    security.declareProtected(ManagePortal, 'getSortedImportSteps')
    def getSortedImportSteps(self):
        if self._exclude_global_steps:
            steps = set()
        else:
            steps = set(_import_step_registry.listSteps())
        steps.update(set(self._import_registry.listSteps()))
        step_infos = [self.getImportStepMetadata(step) for step in steps]
        return tuple(_computeTopologicalSort(step_infos))

    security.declareProtected(ManagePortal, 'getImportStepMetadata')
    def getImportStepMetadata(self, step, default=None):
        """Simple wrapper to query both the global and local step registry."""
        res = self._import_registry.getStepMetadata(step, self)
        if res is self and not self._exclude_global_steps:
            res = _import_step_registry.getStepMetadata(step, default)
        if res is not self:
            return res
        return default

    security.declareProtected(ManagePortal, 'getExportStep')
    def getExportStep(self, step, default=None):
        """Simple wrapper to query both the global and local step registry."""
        res = self._export_registry.getStep(step, self)
        if res is self and not self._exclude_global_steps:
            res = _export_step_registry.getStep(step, self)
        if res is not self:
            return res
        return default

    security.declareProtected(ManagePortal, 'listExportSteps')
    def listExportSteps(self):
        steps = set(self._export_registry.listSteps())
        if not self._exclude_global_steps:
            steps.update(set(_export_step_registry.listSteps()))
        return tuple(steps)

    security.declareProtected(ManagePortal, 'listImportSteps')
    def listImportSteps(self):
        steps = set(self._import_registry.listSteps())
        if not self._exclude_global_steps:
            steps.update(set(_import_step_registry.listSteps()))
        return tuple(steps)


    security.declareProtected(ManagePortal, 'getExportStepMetadata')
    def getExportStepMetadata(self, step, default=None):
        """Simple wrapper to query both the global and local step registry."""
        res = self._export_registry.getStepMetadata(step, self)
        if res is self and not self._exclude_global_steps:
            res = _export_step_registry.getStepMetadata(step, default)
        if res is not self:
            return res
        return default

    security.declareProtected(ManagePortal, 'getToolsetRegistry')
    def getToolsetRegistry(self):
        """ See ISetupTool.
        """
        return self._toolset_registry

    security.declareProtected(ManagePortal, 'runImportStepFromProfile')
    def runImportStepFromProfile(self, profile_id, step_id,
                                 run_dependencies=True, purge_old=None):
        """ See ISetupTool.
        """
        context = self._getImportContext(profile_id, purge_old)

        self.applyContext(context)

        info = self.getImportStepMetadata(step_id)

        if info is None:
            generic_logger.error(
                "No such import step: '%s' Maybe you meant one of %s",
                step_id, str(self.listImportSteps()))
            raise ValueError('No such import step: %s' % step_id)

        dependencies = info.get('dependencies', ())

        messages = {}
        steps = []

        if run_dependencies:
            for dependency in dependencies:
                if dependency not in steps:
                    steps.append(dependency)
        steps.append(step_id)

        full_import = (set(steps) == set(self.getSortedImportSteps()))
        event.notify(
            BeforeProfileImportEvent(self, profile_id, steps, full_import))

        for step in steps:
            message = self._doRunImportStep(step, context)
            messages[step] = message or ''

        message_list = filter(None, [message])
        message_list.extend([ '%s: %s' % x[1:] for x in context.listNotes() ])
        messages[step_id] = '\n'.join(message_list)

        event.notify(
            ProfileImportedEvent(self, profile_id, steps, full_import))

        return {'steps': steps, 'messages': messages}

    security.declareProtected(ManagePortal, 'runAllImportStepsFromProfile')
    def runAllImportStepsFromProfile(self,
                                     profile_id,
                                     purge_old=None,
                                     ignore_dependencies=False,
                                     archive=None,
                                     blacklisted_steps=None):
        """ See ISetupTool.
        """
        __traceback_info__ = profile_id

        result = self._runImportStepsFromContext(
                            purge_old=purge_old,
                            profile_id=profile_id,
                            archive=archive,
                            ignore_dependencies=ignore_dependencies,
                            blacklisted_steps=blacklisted_steps)
        if profile_id is None:
            prefix = 'import-all-from-tar'
        else:
            prefix = 'import-all-%s' % profile_id.replace(':', '_')
        name = self._mangleTimestampName(prefix, 'log')
        self._createReport(name, result['steps'], result['messages'])

        return result

    security.declareProtected(ManagePortal, 'runExportStep')
    def runExportStep(self, step_id):
        """ See ISetupTool.
        """
        return self._doRunExportSteps([step_id])

    security.declareProtected(ManagePortal, 'runAllExportSteps')
    def runAllExportSteps(self):
        """ See ISetupTool.
        """
        return self._doRunExportSteps(self.listExportSteps())

    security.declareProtected(ManagePortal, 'createSnapshot')
    def createSnapshot(self, snapshot_id):
        """ See ISetupTool.
        """
        context = SnapshotExportContext(self, snapshot_id)
        messages = {}
        steps = self.listExportSteps()

        for step_id in steps:

            handler = self.getExportStep(step_id)

            if handler is None:
                logger = logging.getLogger('GenericSetup')
                logger.error('Step %s has an invalid handler' % step_id)
                continue

            messages[step_id] = handler(context)

        return {'steps': steps,
                'messages': messages,
                'url': context.getSnapshotURL(),
                'snapshot': context.getSnapshotFolder()}

    security.declareProtected(ManagePortal, 'compareConfigurations')
    def compareConfigurations(self,
                              lhs_context,
                              rhs_context,
                              missing_as_empty=False,
                              ignore_blanks=False,
                              skip=SKIPPED_FILES,
                             ):
        """ See ISetupTool.
        """
        differ = ConfigDiff(lhs_context,
                            rhs_context,
                            missing_as_empty,
                            ignore_blanks,
                            skip,
                           )

        return differ.compare()

    security.declareProtected(ManagePortal, 'markupComparison')
    def markupComparison(self, lines):
        """ See ISetupTool.
        """
        result = []

        for line in lines.splitlines():

            if line.startswith('** '):

                if line.find('File') > -1:
                    if line.find('replaced') > -1:
                        result.append(('file-to-dir', line))
                    elif line.find('added') > -1:
                        result.append(('file-added', line))
                    else:
                        result.append(('file-removed', line))
                else:
                    if line.find('replaced') > -1:
                        result.append(('dir-to-file', line))
                    elif line.find('added') > -1:
                        result.append(('dir-added', line))
                    else:
                        result.append(('dir-removed', line))

            elif line.startswith('@@'):
                result.append(('diff-range', line))

            elif line.startswith(' '):
                result.append(('diff-context', line))

            elif line.startswith('+'):
                result.append(('diff-added', line))

            elif line.startswith('-'):
                result.append(('diff-removed', line))

            elif line == '\ No newline at end of file':
                result.append(('diff-context', line))

            else:
                result.append(('diff-header', line))

        return '<pre>\n%s\n</pre>' % (
            '\n'.join([('<span class="%s">%s</span>' % (cl, escape(l)))
                                  for cl, l in result]))

    #
    #   ZMI
    #
    manage_options = (
        Folder.manage_options[:1] +
        ({'label': 'Profiles', 'action': 'manage_tool'},
         {'label': 'Import', 'action': 'manage_importSteps'},
         {'label': 'Export', 'action': 'manage_exportSteps'},
         {'label': 'Upgrades', 'action': 'manage_upgrades'},
         {'label': 'Snapshots', 'action': 'manage_snapshots'},
         {'label': 'Comparison', 'action': 'manage_showDiff'},
         {'label': 'Manage', 'action': 'manage_stepRegistry'}) +
        Folder.manage_options[3:]) # skip "View", "Properties"

    security.declareProtected(ManagePortal, 'manage_tool')
    manage_tool = PageTemplateFile('sutProperties', _wwwdir)

    security.declareProtected(ManagePortal, 'manage_updateToolProperties')
    def manage_updateToolProperties(self, context_id,
                                          exclude_global_steps=False,
                                          RESPONSE=None):
        """ Update the tool's settings.
        """
        self.setExcludeGlobalSteps(exclude_global_steps)
        self.setBaselineContext(context_id)

        if RESPONSE is not None:
            RESPONSE.redirect('%s/manage_tool?manage_tabs_message=%s'
                            % (self.absolute_url(), 'Properties+updated.'))

    security.declareProtected(ManagePortal, 'manage_importSteps')
    manage_importSteps = PageTemplateFile('sutImportSteps', _wwwdir)

    security.declareProtected(ManagePortal, 'manage_importSelectedSteps')
    def manage_importSelectedSteps(self, ids, run_dependencies,
                                   context_id=None):
        """ Import the steps selected by the user.
        """
        messages = {}
        if not ids:
            summary = 'No steps selected.'

        else:
            if context_id is None:
                context_id = self.getBaselineContextID()
            steps_run = []
            for step_id in ids:
                result = self.runImportStepFromProfile(context_id,
                                                       step_id,
                                                       run_dependencies)
                steps_run.extend(result['steps'])
                messages.update(result['messages'])

            summary = 'Steps run: %s' % ', '.join(steps_run)

            name = self._mangleTimestampName('import-selected', 'log')
            self._createReport(name, result['steps'], result['messages'])

        return self.manage_importSteps(manage_tabs_message=summary,
                                       messages=messages)

    security.declareProtected(ManagePortal, 'manage_importAllSteps')
    def manage_importAllSteps(self, context_id=None):
        """ Import all steps.
        """
        if context_id is None:
            context_id = self.getBaselineContextID()
        result = self.runAllImportStepsFromProfile(context_id, purge_old=None)

        steps_run = 'Steps run: %s' % ', '.join(result['steps'])

        return self.manage_importSteps(manage_tabs_message=steps_run,
                                       messages=result['messages'])

    security.declareProtected(ManagePortal, 'manage_importExtensions')
    def manage_importExtensions(self, RESPONSE, profile_ids=()):
        """ Import all steps for the selected extension profiles.
        """
        detail = {}
        if len(profile_ids) == 0:
            message = 'Please select one or more extension profiles.'
            RESPONSE.redirect('%s/manage_tool?manage_tabs_message=%s'
                                  % (self.absolute_url(), message))
        else:
            message = 'Imported profiles: %s' % ', '.join(profile_ids)

            for profile_id in profile_ids:

                result = self.runAllImportStepsFromProfile(profile_id)

                for k, v in result['messages'].items():
                    detail['%s:%s' % (profile_id, k)] = v

            return self.manage_importSteps(manage_tabs_message=message,
                                        messages=detail)

    security.declareProtected(ManagePortal, 'manage_importTarball')
    def manage_importTarball(self, tarball):
        """ Import steps from the uploaded tarball.
        """
        if getattr(tarball, 'read', None) is not None:
            tarball = tarball.read()

        result = self.runAllImportStepsFromProfile(None, True, archive=tarball)

        steps_run = 'Steps run: %s' % ', '.join(result['steps'])

        return self.manage_importSteps(manage_tabs_message=steps_run,
                                       messages=result['messages'])

    security.declareProtected(ManagePortal, 'manage_exportSteps')
    manage_exportSteps = PageTemplateFile('sutExportSteps', _wwwdir)

    security.declareProtected(ManagePortal, 'manage_exportSelectedSteps')
    def manage_exportSelectedSteps(self, ids, RESPONSE):
        """ Export the steps selected by the user.
        """
        if not ids:
            RESPONSE.redirect('%s/manage_exportSteps?manage_tabs_message=%s'
                             % (self.absolute_url(), 'No+steps+selected.'))

        result = self._doRunExportSteps(ids)
        RESPONSE.setHeader('Content-type', 'application/x-gzip')
        RESPONSE.setHeader('Content-disposition',
                           'attachment; filename=%s' % result['filename'])
        return result['tarball']

    security.declareProtected(ManagePortal, 'manage_exportAllSteps')
    def manage_exportAllSteps(self, RESPONSE):
        """ Export all steps.
        """
        result = self.runAllExportSteps()
        RESPONSE.setHeader('Content-type', 'application/x-gzip')
        RESPONSE.setHeader('Content-disposition',
                           'attachment; filename=%s' % result['filename'])
        return result['tarball']

    security.declareProtected(ManagePortal, 'manage_upgrades')
    manage_upgrades = PageTemplateFile('setup_upgrades', _wwwdir)

    security.declareProtected(ManagePortal, 'upgradeStepMacro')
    upgradeStepMacro = PageTemplateFile('upgradeStep', _wwwdir)

    security.declareProtected(ManagePortal, 'manage_snapshots')
    manage_snapshots = PageTemplateFile('sutSnapshots', _wwwdir)

    security.declareProtected(ManagePortal, 'listSnapshotInfo')
    def listSnapshotInfo(self):
        """ Return a list of mappings describing available snapshots.

        o Keys include:

          'id' -- snapshot ID

          'title' -- snapshot title or ID

          'url' -- URL of the snapshot folder
        """
        result = []
        snapshots = self._getOb('snapshots', None)

        if snapshots:
            for id, folder in snapshots.objectItems('Folder'):
                result.append({'id': id,
                               'title': folder.title_or_id(),
                               'url': folder.absolute_url()})
        return result

    security.declareProtected(ManagePortal, 'listProfileInfo')
    def listProfileInfo(self, for_=None):
        """ Return a list of mappings describing registered profiles.
        Base profile is listed first, extensions are sorted.

        o Keys include:

          'id' -- profile ID

          'title' -- profile title or ID

          'description' -- description of the profile

          'path' -- path to the profile within its product

          'product' -- name of the registering product
        """
        base = []
        ext = []
        for info in _profile_registry.listProfileInfo(for_):
            if info.get('type', BASE) == BASE:
                base.append(info)
            else:
                ext.append(info)
        ext.sort(lambda x, y: cmp(x['id'], y['id']))
        return base + ext

    security.declareProtected(ManagePortal, 'listContextInfos')
    def listContextInfos(self):
        """ List registered profiles and snapshots.
        """
        def readableType(x):
            if x is BASE:
                return 'base'
            elif x is EXTENSION:
                return 'extension'
            return 'unknown'

        s_infos = [{'id': 'snapshot-%s' % info['id'],
                     'title': info['title'],
                     'type': 'snapshot',
                   }
                    for info in self.listSnapshotInfo()]
        s_infos.sort(key=itemgetter('title'))
        p_infos = [{'id': 'profile-%s' % info['id'],
                    'title': info['title'],
                    'type': readableType(info['type']),
                   }
                   for info in self.listProfileInfo()]
        p_infos.sort(key=itemgetter('title'))

        return tuple(s_infos + p_infos)

    security.declareProtected(ManagePortal, 'getProfileImportDate')
    def getProfileImportDate(self, profile_id):
        """ See ISetupTool.
        """
        prefix = ('import-all-%s-' % profile_id).replace(':', '_')
        candidates = [x for x in self.objectIds('File')
                        if x[:-18] == prefix and x.endswith('.log')]
        if len(candidates) == 0:
            return None
        candidates.sort()
        last = candidates[-1]
        stamp = last[-18:-4]
        return '%s-%s-%sT%s:%s:%sZ' % (stamp[0:4],
                                       stamp[4:6],
                                       stamp[6:8],
                                       stamp[8:10],
                                       stamp[10:12],
                                       stamp[12:14],
                                      )

    security.declareProtected(ManagePortal, 'manage_createSnapshot')
    def manage_createSnapshot(self, RESPONSE, snapshot_id=None):
        """ Create a snapshot with the given ID.

        o If no ID is passed, generate one.
        """
        if snapshot_id is None:
            snapshot_id = self._mangleTimestampName('snapshot')

        self.createSnapshot(snapshot_id)

        return RESPONSE.redirect('%s/manage_snapshots?manage_tabs_message=%s'
                         % (self.absolute_url(), 'Snapshot+created.'))

    security.declareProtected(ManagePortal, 'manage_showDiff')
    manage_showDiff = PageTemplateFile('sutCompare', _wwwdir)

    def manage_downloadDiff(self,
                            lhs,
                            rhs,
                            missing_as_empty,
                            ignore_blanks,
                            RESPONSE,
                           ):
        """ Crack request vars and call compareConfigurations.

        o Return the result as a 'text/plain' stream, suitable for framing.
        """
        comparison = self.manage_compareConfigurations(lhs,
                                                       rhs,
                                                       missing_as_empty,
                                                       ignore_blanks,
                                                      )
        RESPONSE.setHeader('Content-Type', 'text/plain')
        return _PLAINTEXT_DIFF_HEADER % (lhs, rhs, comparison)

    security.declareProtected(ManagePortal, 'manage_compareConfigurations')
    def manage_compareConfigurations(self,
                                     lhs,
                                     rhs,
                                     missing_as_empty,
                                     ignore_blanks,
                                    ):
        """ Crack request vars and call compareConfigurations.
        """
        lhs_context = self._getImportContext(lhs)
        rhs_context = self._getImportContext(rhs)

        return self.compareConfigurations(lhs_context,
                                          rhs_context,
                                          missing_as_empty,
                                          ignore_blanks,
                                         )

    security.declareProtected(ManagePortal, 'manage_stepRegistry')
    manage_stepRegistry = PageTemplateFile('sutManage', _wwwdir)

    security.declareProtected(ManagePortal, 'manage_deleteImportSteps')
    def manage_deleteImportSteps(self, ids, request=None):
        """ Delete selected import steps.
        """
        if request is None:
            request = self.REQUEST
        for id in ids:
            self._import_registry.unregisterStep(id)
        self._p_changed = True
        url = self.absolute_url()
        request.RESPONSE.redirect("%s/manage_stepRegistry" % url)

    security.declareProtected(ManagePortal, 'manage_deleteExportSteps')
    def manage_deleteExportSteps(self, ids, request=None):
        """ Delete selected export steps.
        """
        if request is None:
            request = self.REQUEST
        for id in ids:
            self._export_registry.unregisterStep(id)
        self._p_changed = True
        url = self.absolute_url()
        request.RESPONSE.redirect("%s/manage_stepRegistry" % url)

    #
    # Upgrades management
    #
    security.declareProtected(ManagePortal, 'getLastVersionForProfile')
    def getLastVersionForProfile(self, profile_id):
        """Return the last upgraded version for the specified profile.
        """
        version = self._profile_upgrade_versions.get(profile_id, 'unknown')
        return version

    security.declareProtected(ManagePortal, 'setLastVersionForProfile')
    def setLastVersionForProfile(self, profile_id, version):
        """Set the last upgraded version for the specified profile.
        """
        if isinstance(version, basestring):
            version = tuple(version.split('.'))
        prof_versions = self._profile_upgrade_versions.copy()
        prof_versions[profile_id] = version
        self._profile_upgrade_versions = prof_versions

    security.declareProtected(ManagePortal, 'getVersionForProfile')
    def getVersionForProfile(self, profile_id):
        """Return the registered filesystem version for the specified
        profile.
        """
        return self.getProfileInfo(profile_id).get('version', 'unknown')

    security.declareProtected(ManagePortal, 'profileExists')
    def profileExists(self, profile_id):
        """Check if a profile exists."""
        try:
            self.getProfileInfo(profile_id)
        except KeyError:
            return False
        else:
            return True

    security.declareProtected(ManagePortal, "getProfileInfo")
    def getProfileInfo(self, profile_id):
        if profile_id.startswith("profile-"):
            profile_id = profile_id[len('profile-'):]
        elif profile_id.startswith("snapshot-"):
            profile_id = profile_id[len('snapshot-'):]
        return _profile_registry.getProfileInfo(profile_id)

    security.declareProtected(ManagePortal, 'getDependenciesForProfile')
    def getDependenciesForProfile(self, profile_id):
        if profile_id.startswith("snapshot-"):
            return ()

        if not self.profileExists(profile_id):
            raise KeyError(profile_id)
        try:
            return self.getProfileInfo(profile_id).get('dependencies', ())
        except KeyError:
            return ()

    security.declareProtected(ManagePortal, 'listProfilesWithUpgrades')
    def listProfilesWithUpgrades(self):
        profiles = listProfilesWithUpgrades()
        profiles.sort()
        return profiles

    security.declarePrivate('_massageUpgradeInfo')
    def _massageUpgradeInfo(self, info):
        """Add a couple of data points to the upgrade info dictionary.
        """
        info = info.copy()
        info['haspath'] = info['source'] and info['dest']
        info['ssource'] = '.'.join(info['source'] or ('all',))
        info['sdest'] = '.'.join(info['dest'] or ('all',))
        info['done'] = (not info['proposed'] and
                        info['step'].checker is not None and
                        not info['step'].checker(self))
        return info

    security.declareProtected(ManagePortal, 'listUpgrades')
    def listUpgrades(self, profile_id, show_old=False):
        """Get the list of available upgrades.
        """
        if show_old:
            source = None
        else:
            source = self.getLastVersionForProfile(profile_id)
        upgrades = listUpgradeSteps(self, profile_id, source)
        res = []
        for info in upgrades:
            if type(info) == list:
                subset = []
                for subinfo in info:
                    subset.append(self._massageUpgradeInfo(subinfo))
                res.append(subset)
            else:
                res.append(self._massageUpgradeInfo(info))
        return res

    security.declareProtected(ManagePortal, 'manage_doUpgrades')
    def manage_doUpgrades(self, request=None):
        """Perform all selected upgrade steps.
        """
        if request is None:
            request = self.REQUEST
        logger = logging.getLogger('GenericSetup')
        steps_to_run = request.form.get('upgrades', [])
        profile_id = request.get('profile_id', '')
        step = None
        for step_id in steps_to_run:
            step = _upgrade_registry.getUpgradeStep(profile_id, step_id)
            if step is not None:
                step.doStep(self)
                msg = "Ran upgrade step %s for profile %s" % (step.title,
                                                              profile_id)
                logger.log(logging.INFO, msg)

        # We update the profile version to the last one we have reached
        # with running an upgrade step.
        if step and step.dest is not None and step.checker is None:
            self.setLastVersionForProfile(profile_id, step.dest)

        url = self.absolute_url()
        request.RESPONSE.redirect("%s/manage_upgrades?saved=%s"
                                    % (url, profile_id))

    #
    #   Helper methods
    #
    security.declarePrivate('_getImportContext')
    def _getImportContext(self, context_id, should_purge=None, archive=None):
        """ Crack ID and generate appropriate import context.
        """
        encoding = self.getEncoding()

        if context_id is not None:
            if context_id.startswith('profile-'):
                context_id = context_id[len('profile-'):]
                info = _profile_registry.getProfileInfo(context_id)

                if info.get('product'):
                    path = os.path.join(_getProductPath(info['product']),
                                        info['path'])
                else:
                    path = info['path']
                if should_purge is None:
                    should_purge = (info.get('type') != EXTENSION)
                return DirectoryImportContext(self, path, should_purge,
                                              encoding)

            elif context_id.startswith('snapshot-'):
                context_id = context_id[len('snapshot-'):]
                if should_purge is None:
                    should_purge = True
                return SnapshotImportContext(self, context_id, should_purge,
                                             encoding)

        if archive is not None:
            return TarballImportContext(tool=self,
                                       archive_bits=archive,
                                       encoding='UTF8',
                                       should_purge=should_purge,
                                      )

        raise KeyError('Unknown context "%s"' % context_id)

    security.declarePrivate('_updateImportStepsRegistry')
    def _updateImportStepsRegistry(self, context, encoding):
        """ Update our import steps registry from our profile.
        """
        xml = context.readDataFile(IMPORT_STEPS_XML)
        if xml is None:
            return

        info_list = self._import_registry.parseXML(xml, encoding)

        for step_info in info_list:

            id = step_info['id']
            version = step_info.get('version')
            handler = step_info['handler']
            dependencies = tuple(step_info.get('dependencies', ()))
            title = step_info.get('title', id)
            description = ''.join(step_info.get('description', []))

            self._import_registry.registerStep(id=id,
                                               version=version,
                                               handler=handler,
                                               dependencies=dependencies,
                                               title=title,
                                               description=description,
                                              )

    security.declarePrivate('_updateExportStepsRegistry')
    def _updateExportStepsRegistry(self, context, encoding):
        """ Update our export steps registry from our profile.
        """
        xml = context.readDataFile(EXPORT_STEPS_XML)
        if xml is None:
            return

        info_list = self._export_registry.parseXML(xml, encoding)

        for step_info in info_list:

            id = step_info['id']
            handler = step_info['handler']
            title = step_info.get('title', id)
            description = ''.join(step_info.get('description', []))

            self._export_registry.registerStep(id=id,
                                               handler=handler,
                                               title=title,
                                               description=description,
                                              )

    security.declarePrivate('_doRunImportStep')
    def _doRunImportStep(self, step_id, context):
        """ Run a single import step, using a pre-built context.
        """
        __traceback_info__ = step_id
        marker = object()

        handler = self.getImportStep(step_id)

        if handler is marker:
            raise ValueError('Invalid import step: %s' % step_id)

        if handler is None:
            msg = 'Step %s has an invalid import handler' % step_id
            logger = logging.getLogger('GenericSetup')
            logger.error(msg)
            return 'ERROR: ' + msg

        return handler(context)

    security.declarePrivate('_doRunExportSteps')
    def _doRunExportSteps(self, steps):
        """ See ISetupTool.
        """
        context = TarballExportContext(self)
        messages = {}
        marker = object()

        for step_id in steps:

            handler = self.getExportStep(step_id, marker)

            if handler is marker:
                raise ValueError('Invalid export step: %s' % step_id)

            if handler is None:
                msg = 'Step %s has an invalid export handler' % step_id
                logger = logging.getLogger('GenericSetup')
                logger.error(msg)
                messages[step_id] = msg
            else:
                messages[step_id] = handler(context)

        return {'steps': steps,
                'messages': messages,
                'tarball': context.getArchive(),
                'filename': context.getArchiveFilename()}

    security.declareProtected(ManagePortal, 'getProfileDependencyChain')
    def getProfileDependencyChain(self, profile_id, seen=None):
        if seen is None:
            seen = set()
        elif profile_id in seen:
            return [] # cycle break
        seen.add(profile_id)
        chain = []

        dependencies = self.getDependenciesForProfile(profile_id)
        for dependency in dependencies:
            chain.extend(self.getProfileDependencyChain(dependency, seen))

        chain.append(profile_id)

        return chain

    security.declarePrivate('_runImportStepsFromContext')
    def _runImportStepsFromContext(self,
                                   steps=None,
                                   purge_old=None,
                                   profile_id=None,
                                   archive=None,
                                   ignore_dependencies=False,
                                   seen=None,
                                   blacklisted_steps=None):

        if profile_id is not None and not ignore_dependencies:
            try:
                chain = self.getProfileDependencyChain(profile_id)
            except KeyError, e:
                logger = logging.getLogger('GenericSetup')
                logger.error('Unknown step in dependency chain: %s' % str(e))
                raise
        else:
            chain = [profile_id]
            if seen is None:
                seen = set()
            seen.add(profile_id)

        results = []

        detect_steps = steps is None

        for profile_id in chain:
            context = self._getImportContext(profile_id, purge_old, archive)
            self.applyContext(context)

            if detect_steps:
                steps = self.getSortedImportSteps()

            messages = {}

            event.notify(
                BeforeProfileImportEvent(self, profile_id, steps, True))
            for step in steps:
                if blacklisted_steps and step in blacklisted_steps:
                    message = 'step skipped'
                else:
                    message = self._doRunImportStep(step, context)
                message_list = filter(None, [message])
                message_list.extend([ '%s: %s' % x[1:]
                                      for x in context.listNotes() ])
                messages[step] = '\n'.join(message_list)
                context.clearNotes()

            event.notify(ProfileImportedEvent(self, profile_id, steps, True))

            results.append({'steps': steps, 'messages': messages})

        data = {'steps': [], 'messages': {}}
        for result in results:
            for step in result['steps']:
                if step not in data['steps']:
                    data['steps'].append(step)

            for (step, msg) in result['messages'].items():
                if step in data['messages']:
                    data['messages'][step] += "\n" + msg
                else:
                    data['messages'][step] = msg
        data['steps'] = list(data['steps'])

        return data

    security.declarePrivate('_mangleTimestampName')
    def _mangleTimestampName(self, prefix, ext=None):
        """ Create a mangled ID using a timestamp.
        """
        timestamp = time.gmtime()
        items = (prefix,) + timestamp[:6]

        if ext is None:
            fmt = '%s-%4d%02d%02d%02d%02d%02d'
        else:
            fmt = '%s-%4d%02d%02d%02d%02d%02d.%s'
            items += (ext,)

        return fmt % items

    security.declarePrivate('_createReport')
    def _createReport(self, basename, steps, messages):
        """ Record the results of a run.
        """
        lines = []
        # Create report
        for step in steps:
            lines.append('=' * 65)
            lines.append('Step: %s' % step)
            lines.append('=' * 65)
            msg = messages[step]
            lines.extend(msg.split('\n'))
            lines.append('')

        report = '\n'.join(lines)
        if isinstance(report, unicode):
            report = report.encode('latin-1')

        # BBB: ObjectManager won't allow unicode IDS
        if isinstance(basename, unicode):
            basename = basename.encode('UTF-8')

        name = basename
        index = 0
        while name in self:
            index += 1
            name = basename + '_%i' % index

        file = File(id=name,
                    title='',
                    file=report,
                    content_type='text/plain'
                   )

        self._setObject(name, file)

InitializeClass(SetupTool)


_PLAINTEXT_DIFF_HEADER = """\
Comparing configurations: '%s' and '%s'

%s"""

_TOOL_ID = 'setup_tool'

addSetupToolForm = PageTemplateFile('toolAdd.zpt', _wwwdir)

def addSetupTool(dispatcher, RESPONSE):
    """
    """
    dispatcher._setObject(_TOOL_ID, SetupTool(_TOOL_ID))

    RESPONSE.redirect('%s/manage_main' % dispatcher.absolute_url())
