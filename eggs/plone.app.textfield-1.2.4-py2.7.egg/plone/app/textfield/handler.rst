plone.supermodel handler
========================

If plone.supermodel is installed, this package will register a handler
for the RichText field.

First, let's wire up the package.

    >>> configuration = """\
    ... <configure
    ...      xmlns="http://namespaces.zope.org/zope"
    ...      i18n_domain="plone.app.textfield">
    ...
    ...     <include package="zope.component" file="meta.zcml" />
    ...     <include package="plone.supermodel" />
    ...
    ...     <utility
    ...         component="plone.app.textfield.handler.RichTextHandler"
    ...         name="plone.app.textfield.RichText"
    ...         />
    ...     <adapter factory="plone.app.textfield.handler.RichTextToUnicode" />
    ...
    ... </configure>
    ... """

    >>> from StringIO import StringIO
    >>> from zope.configuration import xmlconfig
    >>> xmlconfig.xmlconfig(StringIO(configuration))

Then, let's test the field

    >>> from zope.component import getUtility
    >>> from plone.app.textfield import RichText

    >>> from plone.supermodel.interfaces import IFieldExportImportHandler
    >>> from plone.supermodel.interfaces import IFieldNameExtractor
    >>> from plone.supermodel.utils import prettyXML

    >>> import datetime
    >>> import plone.supermodel.tests

    >>> field = RichText(__name__=u"dummy", title=u"Test",
    ...     description=u"Test desc", required=False, readonly=True,
    ...     default=u"Test default",
    ...     default_mime_type='text/plain',
    ...     output_mime_type='text/html',
    ...     allowed_mime_types=('text/plain', 'text/html',))
    >>> fieldType = IFieldNameExtractor(field)()
    >>> handler = getUtility(IFieldExportImportHandler, name=fieldType)
    >>> element = handler.write(field, u'dummy', fieldType) #doctest: +ELLIPSIS
    >>> print prettyXML(element)
    <field name="dummy" type="plone.app.textfield.RichText">
      <allowed_mime_types>
        <element>text/plain</element>
        <element>text/html</element>
      </allowed_mime_types>
      <default>Test default</default>
      <default_mime_type>text/plain</default_mime_type>
      <description>Test desc</description>
      <output_mime_type>text/html</output_mime_type>
      <readonly>True</readonly>
      <required>False</required>
      <title>Test</title>
    </field>

To import:

    >>> from lxml import etree
    >>> element = etree.fromstring("""\
    ... <field name="dummy" type="plone.app.textfield.RichText">
    ...   <default>Test default</default>
    ...   <description>Test desc</description>
    ...   <missing_value />
    ...   <readonly>True</readonly>
    ...   <required>False</required>
    ...   <schema>plone.supermodel.tests.IDummy</schema>
    ...   <title>Test</title>
    ...   <default_mime_type>text/plain</default_mime_type>
    ...   <output_mime_type>text/html</output_mime_type>
    ...   <allowed_mime_types>
    ...     <element>text/plain</element>
    ...     <element>text/html</element>
    ...   </allowed_mime_types>
    ... </field>
    ... """)

    >>> reciprocal = handler.read(element)
    >>> reciprocal.__class__
    <class 'plone.app.textfield.RichText'>
    >>> reciprocal.__name__
    'dummy'
    >>> reciprocal.title
    u'Test'
    >>> reciprocal.description
    u'Test desc'
    >>> reciprocal.required
    False
    >>> reciprocal.readonly
    True
    >>> reciprocal.default.raw
    u'Test default'
    >>> reciprocal.missing_value is None
    True
    >>> reciprocal.default_mime_type
    'text/plain'
    >>> reciprocal.output_mime_type
    'text/html'
    >>> reciprocal.allowed_mime_types
    ('text/plain', 'text/html')
