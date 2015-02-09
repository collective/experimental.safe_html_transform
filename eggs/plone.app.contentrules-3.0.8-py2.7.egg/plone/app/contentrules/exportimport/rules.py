from Acquisition import aq_base
from zope.component import adapts
from zope.component import getUtility
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.container.interfaces import INameChooser
from zope.interface import Interface
from zope.interface import implements
from zope.schema.interfaces import IField
from zope.schema.interfaces import ICollection
from zope.schema.interfaces import IFromUnicode

from Products.CMFCore.interfaces import ISiteRoot
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import _getDottedName
from Products.GenericSetup.utils import _resolveDottedName

from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.engine.interfaces import IRuleAssignmentManager
from plone.contentrules.rule.interfaces import IRuleCondition
from plone.contentrules.rule.interfaces import IRuleAction
from plone.contentrules.rule.interfaces import IRuleElement
from plone.contentrules.rule.interfaces import IRuleElementData

from plone.app.contentrules.exportimport.interfaces import IRuleElementExportImportHandler
from plone.app.contentrules.rule import Rule
from plone.app.contentrules.rule import get_assignments
from plone.app.contentrules import api


def as_bool(string, default=False):
    if string is None or not str(string):
        return default
    return string.lower() == 'true'


class PropertyRuleElementExportImportHandler(object):
    """Import portlet assignment settings based on zope.schema properties
    """

    implements(IRuleElementExportImportHandler)
    adapts(Interface)

    def __init__(self, element):
        data = IRuleElementData(element)
        self.element = element
        self.descriptor = getUtility(IRuleElement, name=data.element)

    def import_element(self, node):

        if self.descriptor.schema is None:
            return

        for child in node.childNodes:
            if child.nodeName == 'property':
                self.import_node(self.descriptor.schema, child)

    def export_element(self, doc, node):
        if self.descriptor.schema is None:
            return

        for field_name in self.descriptor.schema:
            field = self.descriptor.schema[field_name]

            if not IField.providedBy(field):
                continue

            child = self.export_field(doc, field)
            node.appendChild(child)


    # Helper methods

    def import_node(self, interface, child):
        """Import a single <property /> node
        """
        property_name = child.getAttribute('name')

        field = interface.get(property_name, None)
        if field is None:
            return

        field = field.bind(self.element)
        value = None

        # If we have a collection, we need to look at the value_type.
        # We look for <element>value</element> child nodes and get the
        # value from there
        if ICollection.providedBy(field):
            value_type = field.value_type
            value = []
            for element in child.childNodes:
                if element.nodeName != 'element':
                    continue
                element_value = self.extract_text(element)
                value.append(self.from_unicode(value_type, element_value))
            value = self.field_typecast(field, value)

        # Otherwise, just get the value of the <property /> node
        else:
            value = self.extract_text(child)
            value = self.from_unicode(field, value)

        field.validate(value)
        field.set(self.element, value)

    def export_field(self, doc, field):
        """Turn a zope.schema field into a node and return it
        """

        field = field.bind(self.element)
        value = field.get(self.element)

        child = doc.createElement('property')
        child.setAttribute('name', field.__name__)

        if value is not None:
            if ICollection.providedBy(field):
                for e in value:
                    list_element = doc.createElement('element')
                    list_element.appendChild(doc.createTextNode(str(e)))
                    child.appendChild(list_element)
            else:
                child.appendChild(doc.createTextNode(unicode(value)))

        return child

    def extract_text(self, node):
        node.normalize()
        text = u""
        for child in node.childNodes:
            if child.nodeType == node.TEXT_NODE:
                text += child.nodeValue
        return text

    def from_unicode(self, field, value):

        # XXX: Bool incorrectly omits to declare that it implements
        # IFromUnicode, even though it does.
        import zope.schema
        if IFromUnicode.providedBy(field) or isinstance(field, zope.schema.Bool):
            return field.fromUnicode(value)
        else:
            return self.field_typecast(field, value)

    def field_typecast(self, field, value):
        # A slight hack to force sequence types to the right type
        typecast = getattr(field, '_type', None)
        if typecast is not None:
            if not isinstance(typecast, (list, tuple)):
                typecast = (typecast, )
            for tc in reversed(typecast):
                if callable(tc):
                    try:
                        value = tc(value)
                        break
                    except:
                        pass
        return value


class RulesXMLAdapter(XMLAdapterBase):
    """In- and exporter for a local portlet configuration
    """
    implements(IBody)
    adapts(ISiteRoot, ISetupEnviron)

    name = 'contentrules'
    _LOGGER_ID = 'contentrules'

    def _exportNode(self):
        """Export rules
        """
        node = self._doc.createElement('contentrules')
        child = self._extractRules()
        if child is not None:
            node.appendChild(child)
        self._logger.info('Content rules exported')
        return node

    def _importNode(self, node):
        """Import rules
        """
        if self.environ.shouldPurge():
            self._purgeRules()
        self._initRules(node)
        self._logger.info('Content rules imported')

    def _purgeRules(self):
        """Purge all registered rules
        """
        storage = queryUtility(IRuleStorage)
        if storage is not None:
            # If we delete a rule, assignments will be removed as well
            for k in list(storage.keys()):
                del storage[k]

    def _initRules(self, node):
        """Import rules from the given node
        """

        site = self.environ.getSite()
        storage = queryUtility(IRuleStorage)
        if storage is None:
            return

        for child in node.childNodes:
            if child.nodeName == 'rule':

                rule = None
                name = child.getAttribute('name')
                if name:
                    rule = storage.get(name, None)

                if rule is None:
                    rule = Rule()

                    if not name:
                        chooser = INameChooser(storage)
                        name = chooser.chooseName(None, rule)

                    storage[name] = rule
                else:
                    # Clear out conditions and actions since we're expecting new ones
                    del rule.conditions[:]
                    del rule.actions[:]

                rule.title = child.getAttribute('title')
                rule.description = child.getAttribute('description')
                event_name = child.getAttribute('event')
                rule.event = _resolveDottedName(event_name)
                if not rule.event:
                    raise ImportError("Can not import %s" % event_name)

                rule.enabled = as_bool(child.getAttribute('enabled'), True)
                rule.stop = as_bool(child.getAttribute('stop-after'))
                rule.cascading = as_bool(child.getAttribute('cascading'))

                # Aq-wrap to enable complex setters for elements below
                # to work

                rule = rule.__of__(site)

                for rule_config_node in child.childNodes:
                    if rule_config_node.nodeName == 'conditions':
                        for condition_node in rule_config_node.childNodes:
                            if not condition_node.nodeName == 'condition':
                                continue

                            type_ = condition_node.getAttribute('type')
                            element_type = getUtility(IRuleCondition, name=type_)
                            if element_type.factory is None:
                                continue

                            condition = element_type.factory()

                            # Aq-wrap in case of complex setters
                            condition = condition.__of__(rule)

                            handler = IRuleElementExportImportHandler(condition)
                            handler.import_element(condition_node)

                            rule.conditions.append(aq_base(condition))

                    elif rule_config_node.nodeName == 'actions':
                        for action_node in rule_config_node.childNodes:
                            if not action_node.nodeName == 'action':
                                continue

                            type_ = action_node.getAttribute('type')
                            element_type = getUtility(IRuleAction, name=type_)
                            if element_type.factory is None:
                                continue

                            action = element_type.factory()

                            # Aq-wrap in case of complex setters
                            action = action.__of__(rule)

                            handler = IRuleElementExportImportHandler(action)
                            handler.import_element(action_node)

                            rule.actions.append(aq_base(action))

            elif child.nodeName == 'assignment':
                location = child.getAttribute('location')
                if location.startswith("/"):
                    location = location[1:]

                try:
                    container = site.unrestrictedTraverse(str(location))
                except KeyError:
                    continue

                name = child.getAttribute('name')
                api.assign_rule(container, name,
                                enabled=as_bool(child.getAttribute('enabled')),
                                bubbles=as_bool(child.getAttribute('bubbles')),
                                insert_before=child.getAttribute('insert-before'),
                                )

    def _extractRules(self):
        """Extract rules to a document fragment
        """

        site = self.environ.getSite()
        storage = queryUtility(IRuleStorage)
        if storage is None:
            return
        fragment = self._doc.createDocumentFragment()

        assignment_paths = set()

        for name, rule in storage.items():
            rule_node = self._doc.createElement('rule')

            rule_node.setAttribute('name', name)
            rule_node.setAttribute('title', rule.title)
            rule_node.setAttribute('description', rule.description)
            rule_node.setAttribute('event', _getDottedName(rule.event))
            rule_node.setAttribute('enabled', str(rule.enabled))
            rule_node.setAttribute('stop-after', str(rule.stop))
            rule_node.setAttribute('cascading', str(rule.cascading))

            # Aq-wrap so that exporting fields with clever getters or
            # vocabularies will work. We also aq-wrap conditions and
            # actions below.

            rule = rule.__of__(site)

            # Add conditions
            conditions_node = self._doc.createElement('conditions')
            for condition in rule.conditions:
                condition_data = IRuleElementData(condition)
                condition = condition.__of__(rule)

                condition_node = self._doc.createElement('condition')
                condition_node.setAttribute('type', condition_data.element)

                handler = IRuleElementExportImportHandler(condition)
                handler.export_element(self._doc, condition_node)
                conditions_node.appendChild(condition_node)
            rule_node.appendChild(conditions_node)

            # Add actions
            actions_node = self._doc.createElement('actions')
            for action in rule.actions:
                action_data = IRuleElementData(action)
                action = action.__of__(rule)

                action_node = self._doc.createElement('action')
                action_node.setAttribute('type', action_data.element)

                handler = IRuleElementExportImportHandler(action)
                handler.export_element(self._doc, action_node)
                actions_node.appendChild(action_node)
            rule_node.appendChild(actions_node)

            fragment.appendChild(rule_node)
            assignment_paths.update(get_assignments(rule))

        # Export assignments last - this is necessary to ensure they
        # are orderd properly

        site_path_length = len('/'.join(site.getPhysicalPath()))
        for path in assignment_paths:
            try:
                container = site.unrestrictedTraverse(path)
            except KeyError:
                continue

            assignable = IRuleAssignmentManager(container, None)
            if assignable is None:
                continue

            location = path[site_path_length:]
            for name, assignment in assignable.items():
                assignment_node = self._doc.createElement('assignment')
                assignment_node.setAttribute('location', location)
                assignment_node.setAttribute('name', name)
                assignment_node.setAttribute('enabled', str(assignment.enabled))
                assignment_node.setAttribute('bubbles', str(assignment.bubbles))
                fragment.appendChild(assignment_node)

        return fragment


def importRules(context):
    """Import content rules
    """
    site = context.getSite()
    importer = queryMultiAdapter((site, context), IBody,
                                 name=u'plone.contentrules')
    if importer is not None:
        filename = '%s%s' % (importer.name, importer.suffix)
        body = context.readDataFile(filename)
        if body is not None:
            importer.filename = filename # for error reporting
            importer.body = body


def exportRules(context):
    """Export content rules
    """
    site = context.getSite()
    exporter = queryMultiAdapter((site, context), IBody,
                                 name=u'plone.contentrules')
    if exporter is not None:
        filename = '%s%s' % (exporter.name, exporter.suffix)
        body = exporter.body
        if body is not None:
            context.writeDataFile(filename, body, exporter.mime_type)
