import re
import datetime

from zope.interface import implements
from zope.component import getUtility
from zope.component import getUtilitiesFor
from zope.component import queryUtility

from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound

from zope.ramcache.interfaces.ram import IRAMCache

from plone.memoize.instance import memoize

from plone.registry.interfaces import IRegistry

from z3c.caching.interfaces import IRulesetType
from z3c.caching.registry import enumerateTypes

from plone.protect import CheckAuthenticator

from plone.caching.interfaces import ICacheSettings
from plone.caching.interfaces import ICachingOperationType

from plone.cachepurging.interfaces import IPurger
from plone.cachepurging.interfaces import ICachePurgingSettings

from plone.cachepurging.utils import isCachePurgingEnabled
from plone.cachepurging.utils import getPathsToPurge
from plone.cachepurging.utils import getURLsToPurge

from plone.app.caching.interfaces import IPloneCacheSettings
from plone.app.caching.interfaces import ICacheProfiles
from plone.app.caching.interfaces import _
from plone.app.caching.browser.edit import EditForm

from Products.GenericSetup.interfaces import BASE, EXTENSION
from Products.CMFCore.utils import getToolByName
from Products.statusmessages.interfaces import IStatusMessage

# Borrowed from zope.schema to avoid an import of a private name
_isuri = re.compile(
    r"[a-zA-z0-9+.-]+:"   # scheme
    r"\S*$"               # non space (should be pickier)
    ).match

class BaseView(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        self.update()
        if self.request.response.getStatus() not in (301, 302):
            return self.render()
        return ''

    def update(self):
        self.errors = {}

        self.registry = getUtility(IRegistry)
        self.settings = self.registry.forInterface(ICacheSettings)
        self.ploneSettings = self.registry.forInterface(IPloneCacheSettings)
        self.purgingSettings = self.registry.forInterface(ICachePurgingSettings)
        self.ramCache = queryUtility(IRAMCache)

        if self.request.method == 'POST':
            CheckAuthenticator(self.request)
            return True
        return False

    def render(self):
        return self.index()

    @property
    @memoize
    def purgingEnabled(self):
        return isCachePurgingEnabled()

class ControlPanel(BaseView):
    """Control panel view
    """

    implements(IPublishTraverse)

    # Used by the publishTraverse() method - see below
    editGlobal = False
    editRuleset = False
    editOperationName = None
    editRulesetName = None

    def publishTraverse(self, request, name):
        """Allow the following types of URLs:

        /
            Render the standard control panel (no publish traverse invoked)

        /edit-operation-global/${operation-name}
            Render an edit form for global operation parameters

        /edit-operation-ruleset/${operation-name}/${ruleset-name}
            Render an edit form for per-ruleset operation parameters
        """

        # Step 1 - find which type of editing we want to do
        if not self.editGlobal and not self.editRuleset:
            if name == 'edit-operation-global':
                self.editGlobal = True
            elif name == 'edit-operation-ruleset':
                self.editRuleset = True
            else:
                raise NotFound(self, name)
            return self # traverse again to get operation name

        # Step 2 - get operation name
        if (self.editGlobal or self.editRuleset) and not self.editOperationName:
            self.editOperationName = name

            if self.editGlobal:

                operation = queryUtility(ICachingOperationType, name=self.editOperationName)
                if operation is None:
                    raise NotFound(self, operation)

                return EditForm(self.context, self.request, self.editOperationName, operation)
            elif self.editRuleset:
                return self # traverse again to get ruleset name
            else:
                raise NotFound(self, name)

        # Step 3 - if this is ruleset traversal, get the ruleset name
        if self.editRuleset and self.editOperationName and not self.editRulesetName:
            self.editRulesetName = name

            operation = queryUtility(ICachingOperationType, name=self.editOperationName)
            if operation is None:
                raise NotFound(self, self.operationName)

            rulesetType = queryUtility(IRulesetType, name=self.editRulesetName)
            if rulesetType is None:
                raise NotFound(self, self.editRulesetName)

            return EditForm(self.context, self.request,
                            self.editOperationName, operation,
                            self.editRulesetName, rulesetType)

        raise NotFound(self, name)

    def update(self):
        if super(ControlPanel, self).update():
            if 'form.button.Save' in self.request.form:
                self.processSave()
            elif 'form.button.Cancel' in self.request.form:
                self.request.response.redirect("%s/plone_control_panel" % self.context.absolute_url())

    def processSave(self):

        form = self.request.form

        # Form data
        enabled            = form.get('enabled', False)
        enableCompression  = form.get('enableCompression', False)
        contentTypesMap    = form.get('contenttypes', {})
        templatesMap       = form.get('templates', {})
        operations         = form.get('operations', {})

        purgingEnabled     = form.get('purgingEnabled', False)
        cachingProxies     = tuple(form.get('cachingProxies', ()))
        purgedContentTypes = tuple(form.get('purgedContentTypes', ()))
        virtualHosting     = form.get('virtualHosting', False)
        domains            = tuple(form.get('domains', ()))

        ramCacheMaxEntries      = form.get('ramCacheMaxEntries', None)
        ramCacheMaxAge          = form.get('ramCacheMaxAge', None)
        ramCacheCleanupInterval = form.get('ramCacheCleanupInterval', None)

        # Settings

        operationMapping          = {}
        contentTypeRulesetMapping = {}
        templateRulesetMapping    = {}

        # Process mappings and validate

        for ruleset, operation in operations.items():

            if not ruleset or not operation:
                continue

            if isinstance(ruleset, unicode): # should be ASCII
                ruleset = ruleset.encode('utf-8')

            if isinstance(operation, unicode): # should be ASCII
                operation = operation.encode('utf-8')

            ruleset = ruleset.replace('-', '.')
            operationMapping[ruleset] = operation

        for ruleset, contentTypes in contentTypesMap.items():

            if not ruleset:
                continue

            if isinstance(ruleset, unicode): # should be ASCII
                ruleset = ruleset.encode('utf-8')

            ruleset = ruleset.replace('-', '.')

            for contentType in contentTypes:

                if not contentType:
                    continue

                if isinstance(contentType, unicode): # should be ASCII
                    contentType = contentType.encode('utf-8')

                if contentType in contentTypeRulesetMapping:
                    self.errors.setdefault('contenttypes', {})[ruleset] = \
                        _(u"Content type ${contentType} is already mapped to the rule ${ruleset}.",
                            mapping={'contentType': self.contentTypesLookup.get(contentType, {}).get('title', contentType),
                                     'ruleset': contentTypeRulesetMapping[contentType]})
                else:
                    contentTypeRulesetMapping[contentType] = ruleset

        for ruleset, templates in templatesMap.items():

            if not ruleset:
                continue

            if isinstance(ruleset, unicode): # should be ASCII
                ruleset = ruleset.encode('utf-8')

            ruleset = ruleset.replace('-', '.')

            for template in templates:

                template = template.strip()

                if not template:
                    continue

                if isinstance(template, unicode): # should be ASCII
                    template = template.encode('utf-8')

                if template in templateRulesetMapping:
                    self.errors.setdefault('templates', {})[ruleset] = \
                        _(u"Template ${template} is already mapped to the rule ${ruleset}.",
                            mapping={'template': template,
                                      'ruleset': templateRulesetMapping[template]})
                else:
                    templateRulesetMapping[template] = ruleset

        # Validate purging settings

        for cachingProxy in cachingProxies:
            if not _isuri(cachingProxy):
                self.errors['cachingProxies'] = _(u"Invalid URL: ${url}", mapping={'url': cachingProxy})

        for domain in domains:
            if not _isuri(domain):
                self.errors['domain'] = _(u"Invalid URL: ${url}", mapping={'url': domain})

        # RAM cache settings

        try:
            ramCacheMaxEntries = int(ramCacheMaxEntries)
        except (ValueError, TypeError,):
            self.errors['ramCacheMaxEntries'] = _(u"An integer is required.")
        else:
            if ramCacheMaxEntries < 0:
                self.errors['ramCacheMaxEntries'] = _(u"A positive number is required.")

        try:
            ramCacheMaxAge = int(ramCacheMaxAge)
        except (ValueError, TypeError,):
            self.errors['ramCacheMaxAge'] = _(u"An integer is required.")
        else:
            if ramCacheMaxAge < 0:
                self.errors['ramCacheMaxAge'] = _(u"A positive number is required.")

        try:
            ramCacheCleanupInterval = int(ramCacheCleanupInterval)
        except (ValueError, TypeError,):
            self.errors['ramCacheCleanupInterval'] = _(u"An integer is required.")
        else:
            if ramCacheMaxAge < 0:
                self.errors['ramCacheCleanupInterval'] = _(u"A positive number is required.")

        # Check for errors
        if self.errors:
            IStatusMessage(self.request).addStatusMessage(_(u"There were errors."), "error")
            return

        # Save settings
        self.settings.enabled = enabled
        self.settings.operationMapping = operationMapping

        self.ploneSettings.enableCompression = enableCompression
        self.ploneSettings.templateRulesetMapping = templateRulesetMapping
        self.ploneSettings.contentTypeRulesetMapping = contentTypeRulesetMapping
        self.ploneSettings.purgedContentTypes = purgedContentTypes

        self.purgingSettings.enabled = purgingEnabled
        self.purgingSettings.cachingProxies = cachingProxies
        self.purgingSettings.virtualHosting = virtualHosting
        self.purgingSettings.domains = domains

        self.ramCache.update(ramCacheMaxEntries, ramCacheMaxAge, ramCacheCleanupInterval)

        IStatusMessage(self.request).addStatusMessage(_(u"Changes saved."), "info")


    # Rule types - used as the index column

    @property
    @memoize
    def ruleTypes(self):
        types = []
        for type_ in enumerateTypes():
            types.append(dict(name=type_.name,
                              title=type_.title or type_.name,
                              description=type_.description,
                              safeName=type_.name.replace('.', '-')))
        types.sort(lambda x,y: cmp(x['title'], y['title']))
        return types

    # Safe access to the main mappings, which may be None - we want to treat
    # that as {} to make TAL expressions simpler. We also need the safeName
    # equivalent name for the key

    @property
    def operationMapping(self):
        return dict(
            [
                (k.replace('.', '-'), v,)
                    for k, v in (self.settings.operationMapping or {}).items()
            ]
        )

    @property
    def templateMapping(self):
        return dict(
            [
                (k, v.replace('.', '-'),)
                    for k, v in (self.ploneSettings.templateRulesetMapping or {}).items()
            ]
        )

    @property
    def contentTypeMapping(self):
        return dict(
            [
                (k, v.replace('.', '-'),)
                    for k, v in (self.ploneSettings.contentTypeRulesetMapping or {}).items()
            ]
        )

    # Type lookups (for accessing settings)

    @property
    @memoize
    def operationTypesLookup(self):
        lookup = {}
        for name, type_ in getUtilitiesFor(ICachingOperationType):
            lookup[name] = dict(
                name=name,
                title=type_.title,
                description=getattr(type_, 'description', ''),
                sort=getattr(type_, 'sort', 100),
                prefix=getattr(type_, 'prefix', None),
                options=getattr(type_, 'options', ()),
                hasOptions=self.hasGlobalOptions(type_),
                type=type_,
            )
        return lookup

    @property
    @memoize
    def contentTypesLookup(self):
        types = {}
        portal_types = getToolByName(self.context, 'portal_types')
        for fti in portal_types.objectValues():
            types[fti.id] = dict(title=fti.title or fti.id, description=fti.description)
        return types

    # Sorted lists (e.g. for drop-downs)

    @property
    @memoize
    def operationTypes(self):
        operations = [v for k, v in self.operationTypesLookup.items()]
        operations.sort(lambda x,y: (cmp(x['sort'], y['sort']) or cmp(x['title'], y['title'])))
        return operations

    @property
    @memoize
    def contentTypes(self):
        types = [
            dict(
                name=name,
                title=info['title'],
                description=info['description']
            ) for name, info in self.contentTypesLookup.items()
        ]
        types.sort(lambda x,y: cmp(x['title'], y['title']))
        return types

    # We store template and content type mappings as template -> ruleset and
    # content type -> ruleset. In the UI, we reverse this, so that the user
    # enters a list of templates and selects a set of content types for each
    # ruleset. This is more natural (whereas the storage is more efficient).
    # These mappings support that UI

    @property
    @memoize
    def reverseContentTypeMapping(self):
        mapping = {}
        for contentType, ruleset in self.contentTypeMapping.items():
            mapping.setdefault(ruleset, []).append(contentType)
        return mapping

    @property
    @memoize
    def reverseTemplateMapping(self):
        mapping = {}
        for template, ruleset in self.templateMapping.items():
            mapping.setdefault(ruleset, []).append(template)
        return mapping

    # For the ruleset mappings page, we need to know whether a particular
    # operation has global and per-ruleset parameters. If there is at least
    # one option set, we consider it to have options.

    def hasGlobalOptions(self, operationType):
        prefix = getattr(operationType, 'prefix', None)
        options = getattr(operationType, 'options', ())

        if not options or not prefix:
            return False

        for option in options:
            if '%s.%s' % (prefix, option,) in self.registry:
                return True

        return False

    def hasRulesetOptions(self, operationType, ruleset):
        prefix = operationType.prefix
        options = operationType.options

        if not options or not prefix:
            return False

        for option in options:
            if '%s.%s.%s' % (prefix, ruleset, option,) in self.registry:
                return True

        return False

class Import(BaseView):
    """The import control panel
    """

    def update(self):
        if super(Import, self).update():
            if 'form.button.Import' in self.request.form:
                self.processImport()

    def processImport(self):
        profile = self.request.form.get('profile', None)
        snapshot = self.request.form.get('snapshot', True)

        if not profile:
            self.errors['profile'] = _(u"You must select a profile to import.")

        if self.errors:
            IStatusMessage(self.request).addStatusMessage(_(u"There were errors."), "error")
            return

        portal_setup = getToolByName(self.context, 'portal_setup')

        # Create a snapshot
        if snapshot:
            snapshotId = "plone.app.caching.beforeimport.%s" % \
                            datetime.datetime.now().isoformat().replace(':', '.')
            portal_setup.createSnapshot(snapshotId)

        # Import the new profile
        portal_setup.runAllImportStepsFromProfile("profile-%s" % profile)

        IStatusMessage(self.request).addStatusMessage(_(u"Import complete."), "info")

    @property
    @memoize
    def profiles(self):
        portal_setup = getToolByName(self.context, 'portal_setup')
        return [profile for profile in portal_setup.listProfileInfo(ICacheProfiles)
                  if profile.get('type', BASE) == EXTENSION and profile.get('for') is not None]

class Purge(BaseView):
    """The purge control panel
    """
    def update(self):
        self.purgeLog = []

        if super(Purge, self).update():
            if 'form.button.Purge' in self.request.form:
                self.processPurge()


    def processPurge(self):

        urls = self.request.form.get('urls', [])
        sync = self.request.form.get('synchronous', True)

        if not urls:
            self.errors['urls'] = _(u"No URLs or paths entered.")

        if self.errors:
            IStatusMessage(self.request).addStatusMessage(_(u"There were errors."), "error")
            return

        purger = getUtility(IPurger)

        serverURL = self.request['SERVER_URL']

        def purge(url):
            if sync:
                status, xcache, xerror = purger.purgeSync(url)

                log = url
                if xcache:
                    log += " (X-Cache header: " + xcache + ")"
                if xerror:
                    log += " -- " + xerror
                self.purgeLog.append(log)
            else:
                purger.purgeAsync(url)
                self.purgeLog.append(url)

        portal_url = getToolByName(self.context, 'portal_url')
        portal = portal_url.getPortalObject()
        portalPath = '/'.join(portal.getPhysicalPath())

        proxies = self.purgingSettings.cachingProxies

        for inputURL in urls:
            if not inputURL.startswith(serverURL): # not in the site
                if '://' in inputURL: # Full URL?
                    purge(inputURL)
                else:                 # Path?
                    for newURL in getURLsToPurge(inputURL, proxies):
                        purge(newURL)
                continue

            physicalPath = relativePath = None
            try:
                physicalPath = self.request.physicalPathFromURL(inputURL)
            except ValueError:
                purge(inputURL)
                continue

            if not physicalPath:
                purge(inputURL)
                continue

            relativePath = physicalPath[len(portalPath):]
            if not relativePath:
                purge(inputURL)
                continue

            obj = portal.unrestrictedTraverse(relativePath, None)
            if obj is None:
                purge(inputURL)
                continue

            for path in getPathsToPurge(obj, self.request):
                for newURL in getURLsToPurge(path, proxies):
                    purge(newURL)

class RAMCache(BaseView):
    """The RAM cache control panel
    """

    def update(self):
        if super(RAMCache, self).update():
            if 'form.button.Purge' in self.request.form:
                self.processPurge()

    def processPurge(self):

        if self.ramCache is None:
            IStatusMessage(self.request).addStatusMessage(_(u"RAM cache not installed."), "error")

        if self.errors:
            IStatusMessage(self.request).addStatusMessage(_(u"There were errors."), "error")
            return

        self.ramCache.invalidateAll()
        IStatusMessage(self.request).addStatusMessage(_(u"Cache purged."), "info")
