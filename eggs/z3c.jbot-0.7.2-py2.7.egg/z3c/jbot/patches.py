from zope.pagetemplate.pagetemplatefile import PageTemplateFile

try:
    from Acquisition.interfaces import IAcquirer
except ImportError:
    IAcquirer = None

import utility
import logging

logger = logging.getLogger('jbot')

# Standard PageTemplateFile

PT_CLASSES = [PageTemplateFile]

try:
    import Products.PageTemplates.PageTemplateFile
    PT_CLASSES.append(Products.PageTemplates.PageTemplateFile.PageTemplateFile)
except:
    pass

registry = {}

def get(template, view=None, cls=None):
    layer = utility.getLayer()
    key = layer, template
    inst = registry.get(key)
    if inst is None:
        cls = type(template)
        inst = registry[key] = cls.__new__(cls)
        inst.__dict__ = template.__dict__.copy()

    for manager in utility.getManagers(layer):
        # register template; this call returns ``True`` if the
        # template was invalidated (changed filename)
        if manager.registerTemplate(inst, template):
            inst._v_last_read = False
            inst.__dict__.pop('_v_template', None)
            break

    if view is not None and IAcquirer is not None:
        if IAcquirer.providedBy(inst) and IAcquirer.providedBy(view):
            return inst.__of__(view)

    return inst

# five.pt / Chameleon
try:
    from five.pt.pagetemplate import ViewPageTemplateFile as \
         pt_class
except ImportError:
    pass
else:
    five_bind = pt_class.__get__

    def get_and_bind(template, view=None, cls=None):
        inst = get(template, view, cls)
        if inst._v_last_read is False:
            inst.registry.purge()
            inst.read()
        return five_bind(inst, view, cls)

    pt_class.__get__ = get_and_bind
    logger.debug(repr(pt_class))

    del pt_class

# Zope 2.12 ViewPageTemplateFile; note that we import
# ``BoundPageTemplate`` to provoke an import-error on Zope 2.10.
try:
    from Products.Five.browser.pagetemplatefile import \
         ViewPageTemplateFile as pt_class
    zope_bind = pt_class.__get__
except ImportError:
    pass
except AttributeError:
    pass
else:
    def five_get_and_bind(template, view=None, cls=None):
        inst = get(template, view, cls)
        if inst._v_last_read is False:
            inst.read()
        return zope_bind(inst, view, cls)

    pt_class.__get__ = five_get_and_bind
    logger.debug(repr(pt_class))

    del pt_class

# zope.browserpage ViewPageTemplateFile
try:
    from zope.browserpage.viewpagetemplatefile import \
        ViewPageTemplateFile as pt_class
    browserpage_bind = pt_class.__get__
except ImportError:
    pass
except AttributeError:
    pass
else:
    def get_and_bind(template, view=None, cls=None):
        inst = get(template, view, cls)
        if inst._v_last_read is False:
            inst.read()
        return browserpage_bind(inst, view, cls)

    pt_class.__get__ = get_and_bind
    logger.debug(repr(pt_class))

    del pt_class


for pt_class in PT_CLASSES:
    pt_class.__get__ = get
    logger.debug(repr(pt_class))

# CMF skin layer resources
try:
    from Products.CMFCore.FSObject import FSObject as fs_class
except ImportError:
    pass
else:
    of = fs_class.__of__

    def get_skin_obj(obj, view=None, cls=None):
        layer = utility.getLayer()
        key = layer, obj
        inst = registry.get(key)
        if inst is None:
            cls = obj.__class__
            inst = registry[key] = cls.__new__(cls)
            inst.__dict__ = obj.__dict__.copy()

        for manager in utility.getManagers(layer):
            # register template; this call returns ``True`` if the
            # template was invalidated (changed filename)
            if manager.registerTemplate(inst, obj):
                inst._parsed = False
                inst.getObjectFSPath()

        return of(inst, view)

    def get_filename(obj, *args):
        return obj._filepath

    def set_filename(obj, value, *args):
        obj._filepath = value

    fs_class.__of__ = get_skin_obj
    fs_class.filename = property(get_filename, set_filename)

    logger.debug(repr(fs_class))
