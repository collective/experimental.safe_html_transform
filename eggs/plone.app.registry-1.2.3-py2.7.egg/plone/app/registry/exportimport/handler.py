from zope.component import queryUtility
from zope.schema import getFieldNames

from lxml import etree

from zope.dottedname.resolve import resolve

from plone.registry.interfaces import IRegistry
from plone.registry.interfaces import IPersistentField
from plone.registry.interfaces import IInterfaceAwareRecord
from plone.registry.interfaces import IFieldRef

from plone.registry import Record
from plone.registry import FieldRef

from plone.supermodel.interfaces import IFieldExportImportHandler
from plone.supermodel.interfaces import IFieldNameExtractor
from plone.supermodel.interfaces import I18N_NAMESPACE
from plone.supermodel.debug import parseinfo

from plone.supermodel.utils import prettyXML, elementToValue, valueToElement, ns

_marker = object()


def shouldPurgeList(value_node, key):
    for child in value_node:
        attrib = child.attrib
        if attrib.get('key') == key:
            if attrib.get('purge', 'true').lower() == 'false':
                return False
            else:
                return True
    return True


def importRegistry(context):

    logger = context.getLogger('plone.app.registry')
    registry = queryUtility(IRegistry)

    if registry is None:
        logger.info("Cannot find registry")
        return

    body = context.readDataFile('registry.xml')
    if body is not None:
        importer = RegistryImporter(registry, context)
        importer.importDocument(body)


def exportRegistry(context):

    logger = context.getLogger('plone.app.registry')
    registry = queryUtility(IRegistry)

    if registry is None:
        logger.info("Cannot find registry")
        return

    exporter = RegistryExporter(registry, context)
    body = exporter.exportDocument()
    if body is not None:
        context.writeDataFile('registry.xml', body, 'text/xml')


class RegistryImporter(object):
    """Helper classt to import a registry file
    """

    LOGGER_ID = 'plone.app.registry'

    def __init__(self, context, environ):
        self.context = context
        self.environ = environ
        self.logger = environ.getLogger(self.LOGGER_ID)

    def importDocument(self, document):
        tree = etree.fromstring(document)

        if self.environ.shouldPurge():
            self.context.records.clear()

        i18n_domain = tree.attrib.get(ns('domain', I18N_NAMESPACE))
        if i18n_domain:
            parseinfo.i18n_domain = i18n_domain

        for node in tree:
            if not isinstance(node.tag, str):
                continue
            if node.tag.lower() == 'record':
                self.importRecord(node)
            elif node.tag.lower() == 'records':
                self.importRecords(node)

        parseinfo.i18n_domain = None

    def importRecord(self, node):
        name = node.get('name', '')
        if node.get('delete') is not None:
            self.logger.warning(u"The 'delete' attribute of <record /> nodes "
                                u"is deprecated, it should be replaced with "
                                u"'remove'.")
        remove = node.get('remove', node.get('delete', 'false'))

        interfaceName = node.get('interface', None)
        fieldName = node.get('field', None)

        if not name and (interfaceName and fieldName):
            prefix = node.get('prefix', None)
            if prefix is None:
                prefix = interfaceName

            name = "%s.%s" % (prefix, fieldName)

        if not name:
            raise NameError("No name given for <record /> node!")

        # Unicode is not supported
        name = str(name)

        # Handle deletion and quit
        if remove.lower() == 'true':
            if name in self.context.records:
                del self.context.records[name]
                self.logger.info("Removed record %s." % name)
            else:
                self.logger.warning("Record %s was marked for deletion, but was not found." % name)
            return

        # See if we have an existing record
        existing_record = self.context.records.get(name, None)

        interface = None
        field = None
        value = _marker
        value_purge = True

        # If we are given an interface and field name, try to resolve them
        if interfaceName and fieldName:
            try:
                interface = resolve(interfaceName)
                field = IPersistentField(interface[fieldName])
            except ImportError:
                self.logger.warning("Failed to import interface %s for \
                    record %s" % (interfaceName, name))
                interface = None
                field = None
            except KeyError:
                self.logger.warning("Interface %s specified for record %s has \
                    no field %s." % (interfaceName, name, fieldName))
                interface = None
                field = None
            except TypeError:
                self.logger.warning("Field %s in interface %s specified for \
                    record %s cannot be used as a persistent field." % (fieldName, interfaceName, name))
                interface = None
                field = None

        # Find field and value nodes

        field_node = None
        value_node = None

        for child in node:
            if not isinstance(child.tag, str):
                continue
            elif child.tag.lower() == 'field':
                field_node = child
            elif child.tag.lower() == 'value':
                value_node = child

        # Let field not potentially override interface[fieldName]
        if field_node is not None:
            field_ref = field_node.attrib.get('ref', None)
            if field_ref is not None:
                # We have a field reference
                if field_ref not in self.context:
                    raise KeyError(u"Record %s references field for record %s, \
                        which does not exist" % (name, field_ref))
                ref_record = self.context.records[field_ref]
                field = FieldRef(field_ref, ref_record.field)
            else:
                # We have a standard field
                field_type = field_node.attrib.get('type', None)
                field_type_handler = queryUtility(IFieldExportImportHandler, name=field_type)
                if field_type_handler is None:
                    raise TypeError("Field of type %s used for record %s is not supported." % (field_type, name))
                else:
                    field = field_type_handler.read(field_node)
                    if not IPersistentField.providedBy(field):
                        raise TypeError("Only persistent fields may be imported. \
                            %s used for record %s is invalid." % (field_type, name))

        if field is not None and not IFieldRef.providedBy(field):

            # Set interface name and fieldName, if applicable
            field.interfaceName = interfaceName
            field.fieldName = fieldName

        # Fall back to existing record if neither a field node nor the
        # interface yielded a field

        change_field = True

        if field is None and existing_record is not None:
            change_field = False
            field = existing_record.field

        if field is None:
            raise ValueError("Cannot find a field for the record %s. Add a \
                <field /> element or reference an interface and field name." % name)

        # Extract the value

        if value_node is not None:
            value_purge = value_node.attrib.get('purge', '').lower() != 'false'
            value = elementToValue(field, value_node, default=_marker)

        # Now either construct or update the record

        if value is _marker:
            value = field.default
            value_purge = True

        if existing_record is not None:
            if change_field:
                existing_record.field = field
            existing_value = existing_record.value
            if change_field or value != existing_value:

                if not value_purge and type(value) == type(existing_value):
                    if isinstance(value, list):
                        value = existing_value + [v for v in value if v not in existing_value]
                    elif isinstance(value, tuple):
                        value = existing_value + tuple([v for v in value if v not in existing_value])
                    elif isinstance(value, (set, frozenset, )):
                        value = existing_value.union(value)
                    elif isinstance(value, dict):
                        for key, value in value.items():
                            # check if value is list, if so, let's add
                            # instead of overridding
                            if type(value) == list:
                                if key in existing_value and \
                                        not shouldPurgeList(value_node, key):
                                    existing = existing_value[key]
                                    for item in existing:
                                        # here, we'll remove existing items
                                        # point is that we don't want duplicates
                                        # and don't want to reorder
                                        if item in value:
                                            value.remove(item)
                                    existing.extend(value)
                                    value = existing
                            existing_value[key] = value

                        value = existing_value

                existing_record.value = value
        else:
            self.context.records[name] = Record(field, value)

    def importRecords(self, node):

        # May raise ImportError if interface can't be found or KeyError if
        # attribute is missing.

        interfaceName = node.attrib.get('interface', None)
        if interfaceName is None:
            raise KeyError(u"A <records /> node must have an 'interface' attribute.")

        prefix = node.attrib.get('prefix', None) # None means use interface.__identifier__
        
        if node.attrib.get('delete') is not None:
            self.logger.warning(u"The 'delete' attribute of <record /> nodes "
                                u"is deprecated, it should be replaced with "
                                u"'remove'.")
        remove = node.attrib.get('remove', node.attrib.get('delete', 'false')).lower() == 'true'

        # May raise ImportError
        interface = resolve(interfaceName)

        omit = []
        values = [] # Fields that should have their value set as they don't exist yet

        for child in node:
            if not isinstance(child.tag, str):
                continue
            elif child.tag.lower() == 'omit':
                if child.text:
                    omit.append(unicode(child.text))
            elif child.tag.lower() == 'value':
                values.append(child)

        if remove and values:
            raise ValueError("A <records /> node with 'remove=\"true\"' must not contain "
                             "<value /> nodes.")
        elif remove:
            for f in getFieldNames(interface):
                if f in omit:
                    continue

                child = etree.Element('value', key=f, purge='True')
                values.append(child)

        # May raise TypeError
        self.context.registerInterface(interface, omit=tuple(omit), prefix=prefix)

        if not values and not remove:
            # Skip out if there are no value records to handle
            return

        # The prefix we ended up needs to be found
        if prefix is None:
            prefix = interface.__identifier__

        for value in values:
            field = etree.Element("record", interface=interface.__identifier__, field=value.attrib["key"], prefix=prefix, remove=repr(remove).lower())
            field.append(value)
            self.importRecord(field)


class RegistryExporter(object):

    LOGGER_ID = 'plone.app.registry'

    def __init__(self, context, environ):
        self.context = context
        self.environ = environ
        self.logger = environ.getLogger(self.LOGGER_ID)

    def exportDocument(self):
        root = etree.Element('registry')

        for record in self.context.records.values():
            node = self.exportRecord(record)
            root.append(node)

        return prettyXML(root)

    def exportRecord(self, record):

        node = etree.Element('record')
        node.attrib['name'] = record.__name__

        if IInterfaceAwareRecord.providedBy(record):
            node.attrib['interface'] = record.interfaceName
            node.attrib['field'] = record.fieldName

        # write field

        field = record.field
        if IFieldRef.providedBy(field):
            field_element = etree.Element('field')
            field_element.attrib['ref'] = field.recordName
            node.append(field_element)
        else:
            field_type = IFieldNameExtractor(record.field)()
            handler = queryUtility(IFieldExportImportHandler, name=field_type)
            if handler is None:
                self.logger.warning("Field type %s specified for record %s \
                    cannot be exported" % (field_type, record.__name__))
            else:
                field_element = handler.write(record.field, None, field_type, elementName='field')
                node.append(field_element)

        # write value

        value_element = valueToElement(record.field, record.value, name='value', force=True)
        node.append(value_element)

        return node
