from lxml import etree, html
from repoze.xmliter.serializer import XMLSerializer

def getXMLSerializer(iterable, parser=etree.XMLParser, serializer=etree.tostring,
                     pretty_print=False, encoding=None, doctype=None):
    """Turn the given iterable into an XMLSerializer. If it is already an
    XMLSerializer, return as-is. Otherwise, parse the input using with the
    given parser in feed-parser mode and initalize an XMLSerializer with the
    appropriate serializer function and pretty printing flag.
    """
    if isinstance(iterable, XMLSerializer):
        return iterable
    
    p = parser(encoding=encoding)
    for chunk in iterable:
        p.feed(chunk)
    root = p.close()
    
    return XMLSerializer(root.getroottree(), serializer, pretty_print, doctype=doctype)

def getHTMLSerializer(iterable, pretty_print=False, encoding=None, doctype=None):
    """Convenience method to create an XMLSerializer instance using the HTML
    parser and string serialization. If the doctype is XHTML or XHTML
    transitional, use the XML serializer.
    """
    serializer = getXMLSerializer(
                        iterable,
                        parser=html.HTMLParser,
                        serializer=html.tostring,
                        pretty_print=pretty_print,
                        encoding=encoding,
                        doctype=doctype,
                    )
    if serializer.tree.docinfo.doctype and 'XHTML' in serializer.tree.docinfo.doctype:
        serializer.serializer = etree.tostring
    
    return serializer
