import lxml.etree
import re

doctype_re = re.compile(r"^<!DOCTYPE\s[^>]+>\s*", re.MULTILINE)

class XMLSerializer(object):
    
    def __init__(self, tree, serializer=None, pretty_print=False, doctype=None):
        if serializer is None:
            serializer = lxml.etree.tostring
        self.tree = tree
        self.serializer = serializer
        self.pretty_print = pretty_print
        if doctype and not doctype.endswith('\n'):
            doctype = doctype + '\n'
        self.doctype = doctype

    def serialize(self, encoding=None):
        # Defer to the xsl:output settings if appropriate
        if isinstance(self.tree, lxml.etree._XSLTResultTree):
            if encoding is unicode:
                result = unicode(self.tree)
            else:
                result = str(self.tree)
        else:
            result = self.serializer(self.tree, encoding=encoding, pretty_print=self.pretty_print)
        if self.doctype is not None:
            result, subs = doctype_re.subn(self.doctype, result, 1)
            if not subs:
                result = self.doctype + result
        return result

    def __iter__(self):
        return iter((str(self),))

    def __str__(self):
        return self.serialize()

    def __unicode__(self):
        return self.serialize(unicode)

    def __len__(self):
        return 1
