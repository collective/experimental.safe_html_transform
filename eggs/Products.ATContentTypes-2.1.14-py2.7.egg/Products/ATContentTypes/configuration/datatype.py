from Products.CMFCore import permissions as CMFCorePermissions
from AccessControl import Permissions as ZopePermissions
from ZConfig.datatypes import IdentifierConversion
from ZConfig.datatypes import stock_datatypes

_marker = object()


def _getValueFromModule(module, key):
    var = getattr(module, key, _marker)
    if key is _marker:
        raise ValueError, "%s doesn't have an attribute %s" % (module, key)
    return var


def _getValueFromDottedName(dotted_name):
    parts = dotted_name.split('.')
    module_name = '.'.join(parts[:-1])
    key = parts[-1]
    try:
        module = __import__(module_name, globals(), locals(), [key])
    except ImportError, msg:
        raise ValueError, str(msg)
    return _getValueFromModule(module, key)


def permission_handler(value):
    """Parse a permission

    Valid value are:
        cmf.NAME - Products.CMFCore.permissions
        zope.NAME - AccessControl.Permissions
        aDottedName
    """
    if value.startswith('cmf.'):
        permission = _getValueFromModule(CMFCorePermissions, value[4:])
    elif value.startswith('zope.'):
        permission = _getValueFromModule(ZopePermissions, value[5:])
    else:
        permission = _getValueFromDottedName(value)
    if not isinstance(permission, basestring):
        raise ValueError, 'Permission %s is not a string: %s' % (permission,
            type(permission))
    return permission


def identifier_none(value):
    if value == 'None':
        return None
    return IdentifierConversion()(value)


def byte_size_in_mb(value):
    """Byte size handler for max size validator
    """
    if value.lower() == 'no':
        return 0.0
    byte_size = stock_datatypes["byte-size"]
    v = byte_size(value)
    return float(v) / (1024.0 ** 2)


def image_dimension(value):
    """Image dimension data type

    Splits a value of "200, 400" into two ints of (200, 400)
    """
    if value.count(',') != 1:
        raise ValueError, "Width and height must be seperated by a comma"
    w, h = value.split(',')
    w = int(w)
    h = int(h)
    return (w, h)


def image_dimension_or_no(value):
    """Image dimension data type with support for no

    Either "no" or (0, 0) results into None
    """
    if value.lower() == 'no':
        return None
    w, h = image_dimension(value)
    if (w, h) == (0, 0):
        return None
    return (w, h)


def pil_algo(value):
    """Get PIL image filter algo from PIL.Image
    """
    try:
        import PIL.Image
    except ImportError:
        return None

    value = value.upper()
    available = ('NEAREST', 'BILINEAR', 'BICUBIC', 'ANTIALIAS')
    if value not in available:
        raise ValueError, "unknown algo %s" % value
    import PIL.Image
    return getattr(PIL.Image, value)


class BaseFactory(object):
    """Basic factory
    """

    def __init__(self, section):
        self.name = section.getSectionName()
        #self._parsed = False
        self._section = section
        self._names = {}
        self._parse()

    #def __call__(self):
    #    if not self._parsed:
    #        self._parse()
    #    return self

    def set(self, name, value):
        self._names[name] = 1
        setattr(self, name, value)

    def _parse(self):
        raise NotImplementedError


class MxTidy(BaseFactory):
    """data handler for mx tidy settings

    sets enable and options
    """

    def _parse(self):
        sec = self._section
        self.set('enable', sec.enable)
        cfg = {}
        for id in ('char_encoding', 'drop_empty_paras', 'drop_font_tags',
          'indent_spaces', 'input_xml', 'output_xhtml', 'quiet', 'show_warnings',
          'tab_size', 'word_2000', 'wrap'):
            cfg[id] = getattr(sec, id)
        self.set('options', cfg)


class Archetype(BaseFactory):
    """data handler for an archetype option
    """

    def _parse(self):
        sec = self._section
        self.set('max_file_size', sec.max_file_size)
        self.set('max_image_dimension', sec.max_image_dimension)
        self.set('allow_document_upload', sec.allow_document_upload)

        ct = sec.contenttypes
        if ct is not None:
            allowed = tuple(ct.allowed_content_types)
            default = ct.default_content_type

            if default not in allowed:
                raise ValueError, "Default %s is not in %s" % (default, ct)

            self.set('default_content_type', default)
            self.set('allowed_content_types', allowed)


class Feature(BaseFactory):
    """data handler for a feature
    """

    def _parse(self):
        sec = self._section
        self.set('enable', sec.enable)
