from lxml import etree
from z3c.relationfield.relation import TemporaryRelationValue
from z3c.relationfield.interfaces import IRelationList
from z3c.relationfield.interfaces import IRelation
from z3c.schema2xml import IXMLGenerator
from zope.component import adapter
from zope.interface import implements


@adapter(IRelationList)
class RelationListGenerator(object):
    """Export a relation list to XML.
    """

    implements(IXMLGenerator)

    def __init__(self, context):
        self.context = context

    def output(self, container, value):
        element = etree.SubElement(container, self.context.__name__)
        field = self.context.value_type
        if value is not None:
            for v in value:
                IXMLGenerator(field).output(element, v)

    def input(self, element):
        field = self.context.value_type
        return [
            IXMLGenerator(field).input(sub_element)
            for sub_element in element]


@adapter(IRelation)
class RelationGenerator(object):
    """Eport a relation to XML.
    """

    implements(IXMLGenerator)

    def __init__(self, context):
        self.context = context

    def output(self, container, value):
        element = etree.SubElement(container, self.context.__name__)
        if value is not None:
            element.text = value.to_path

    def input(self, element):
        if element.text is None:
            return None
        path = element.text
        return TemporaryRelationValue(path)
