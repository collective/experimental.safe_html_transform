##############################################################################
#
# Copyright (c) 2001 Zope Foundation and Contributors
# Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this
# distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import unittest

from OFS.Folder import Folder
from Acquisition import Implicit

class DummyFolder(Folder):
    pass

class DummyPlugin(Implicit):
    pass


class PluginRegistryTests(unittest.TestCase):

    def _getTargetClass(self):

        from Products.PluginRegistry.PluginRegistry import PluginRegistry

        return PluginRegistry

    def _makeOne(self, plugin_info=None, *args, **kw):

        if plugin_info is None:
            plugin_info, IFoo, IBar = self._makePluginInfo()

        return self._getTargetClass()(plugin_info, *args, **kw)

    def _makePluginInfo(self):

        from zope.interface import Interface

        class IFoo(Interface):
            def foo():
                """ Foo. """

        class IBar(Interface):
            def bar():
                """ Bar. """

        _PLUGIN_INFO = ((IFoo, 'IFoo', 'foo', 'Foo test'),
                        (IBar, 'IBar', 'bar', 'Bar test'),
                       )

        return _PLUGIN_INFO, IFoo, IBar

    def test_class_conforms_to_IPluginRegistry(self):
        from zope.interface.verify import verifyClass
        from Products.PluginRegistry.interfaces import IPluginRegistry
        verifyClass(IPluginRegistry, self._getTargetClass())

    def test_instance_conforms_to_IPluginRegistry(self):
        from zope.interface.verify import verifyObject
        from Products.PluginRegistry.interfaces import IPluginRegistry
        verifyObject(IPluginRegistry, self._makeOne())

    def test_listPlugins_miss(self):
        from zope.interface import Interface

        class INonesuch(Interface):
            pass

        preg = self._makeOne(())
        self.assertRaises(KeyError, preg.listPlugins, INonesuch)

    def test_listPluginIds_miss(self):
        from zope.interface import Interface

        class INonesuch(Interface):
            pass

        preg = self._makeOne(())
        self.assertRaises(KeyError, preg.listPluginIds, INonesuch)

    def test_listPlugins_hit(self):
        plugin_info, IFoo, IBar = self._makePluginInfo()
        preg = self._makeOne(plugin_info)
        self.assertEqual(len(preg.listPluginIds(IFoo)), 0)

    def test_listPluginIds_hit(self):
        plugin_info, IFoo, IBar = self._makePluginInfo()
        preg = self._makeOne(plugin_info)
        self.assertEqual(len(preg.listPluginIds(IFoo)), 0)

    def test_listPluginTypeInfo_empty(self):
        pref = self._makeOne(())

        pti = pref.listPluginTypeInfo()
        self.assertEqual(len(pti), 0)

    def test_listPluginTypeInfo_filled(self):
        plugin_info, IFoo, IBar = self._makePluginInfo()
        pref = self._makeOne(plugin_info)

        pti = pref.listPluginTypeInfo()
        self.assertEqual(len(pti), 2)
        self.assertEqual(pti[0]['interface'], IFoo)
        self.assertEqual(pti[0]['title'], 'foo')
        self.assertEqual(pti[1]['interface'], IBar)
        self.assertEqual(pti[1]['title'], 'bar')

    def test_activatePlugin_no_child(self):
        plugin_info, IFoo, IBar = self._makePluginInfo()
        parent = DummyFolder()
        preg = self._makeOne(plugin_info).__of__(parent)

        self.assertRaises(AttributeError, preg.activatePlugin, IFoo,
                           'foo_plugin')

    def test_activatePluginInterface_non_conforming_interface(self):
        plugin_info, IFoo, IBar = self._makePluginInfo()
        parent = DummyFolder()
        foo_plugin = DummyPlugin()
        parent._setObject('foo_plugin', foo_plugin)
        preg = self._makeOne(plugin_info).__of__(parent)

        self.assertRaises(ValueError, preg.activatePlugin, IFoo, 'foo_plugin')

    def test_activatePlugin_valid_child(self):
        from zope.interface import directlyProvides
        plugin_info, IFoo, IBar = self._makePluginInfo()
        parent = DummyFolder()
        foo_plugin = DummyPlugin()
        directlyProvides(foo_plugin,  (IFoo,))
        parent._setObject('foo_plugin', foo_plugin)

        preg = self._makeOne(plugin_info).__of__(parent)

        preg.activatePlugin(IFoo, 'foo_plugin')

        idlist = preg.listPluginIds(IFoo)
        self.assertEqual(len(idlist), 1)
        self.assertEqual(idlist[0], 'foo_plugin')

        plugins = preg.listPlugins(IFoo)
        self.assertEqual(len(plugins), 1)
        plugin = plugins[0]
        self.assertEqual(plugin[0], 'foo_plugin')
        self.assertEqual(plugin[1], preg.foo_plugin)

    def test_activatePlugin_then_remove_interface(self):
        from zope.interface import directlyProvides
        plugin_info, IFoo, IBar = self._makePluginInfo()
        parent = DummyFolder()
        foo_plugin = DummyPlugin()
        directlyProvides(foo_plugin,  (IFoo,))
        parent._setObject('foo_plugin', foo_plugin)

        preg = self._makeOne(plugin_info).__of__(parent)

        preg.activatePlugin(IFoo, 'foo_plugin')

        replacement = DummyPlugin()
        parent._delObject('foo_plugin')
        parent._setObject('foo_plugin', replacement)

        idlist = preg.listPluginIds(IFoo)
        self.assertEqual(len(idlist), 1)  # note discrepancy

        plugins = preg.listPlugins(IFoo)
        self.assertEqual(len(plugins), 0)

    def test_deactivatePlugin(self):
        from zope.interface import directlyProvides
        plugin_info, IFoo, IBar = self._makePluginInfo()
        parent = DummyFolder()
        foo_plugin = DummyPlugin()
        directlyProvides(foo_plugin, (IFoo,))
        parent._setObject('foo_plugin', foo_plugin)

        bar_plugin = DummyPlugin()
        directlyProvides(bar_plugin, (IFoo,))
        parent._setObject('bar_plugin', bar_plugin)

        baz_plugin = DummyPlugin()
        directlyProvides(baz_plugin, (IFoo,))
        parent._setObject('baz_plugin', baz_plugin)

        preg = self._makeOne(plugin_info).__of__(parent)

        preg.activatePlugin(IFoo, 'foo_plugin')
        preg.activatePlugin(IFoo, 'bar_plugin')
        preg.activatePlugin(IFoo, 'baz_plugin')

        preg.deactivatePlugin(IFoo, 'bar_plugin')

        idlist = preg.listPluginIds(IFoo)
        self.assertEqual(len(idlist), 2)
        self.assertEqual(idlist[0], 'foo_plugin')
        self.assertEqual(idlist[1], 'baz_plugin')

    def test_movePluginsUp(self):
        from zope.interface import directlyProvides
        plugin_info, IFoo, IBar = self._makePluginInfo()
        parent = DummyFolder()
        foo_plugin = DummyPlugin()
        directlyProvides(foo_plugin, (IFoo,))
        parent._setObject('foo_plugin', foo_plugin)

        bar_plugin = DummyPlugin()
        directlyProvides(bar_plugin, (IFoo,))
        parent._setObject('bar_plugin', bar_plugin)

        baz_plugin = DummyPlugin()
        directlyProvides(baz_plugin, (IFoo,))
        parent._setObject('baz_plugin', baz_plugin)

        preg = self._makeOne(plugin_info).__of__(parent)

        preg.activatePlugin(IFoo, 'foo_plugin')
        preg.activatePlugin(IFoo, 'bar_plugin')
        preg.activatePlugin(IFoo, 'baz_plugin')

        self.assertRaises(ValueError,
                          preg.movePluginsUp, IFoo, ('quux_plugin',))

        preg.movePluginsUp(IFoo, ('bar_plugin', 'baz_plugin'))

        idlist = preg.listPluginIds(IFoo)
        self.assertEqual(len(idlist), 3)

        self.assertEqual(idlist[0], 'bar_plugin')
        self.assertEqual(idlist[1], 'baz_plugin')
        self.assertEqual(idlist[2], 'foo_plugin')

        # Moving the top plugin up should not change anything.
        preg.movePluginsUp(IFoo, ('bar_plugin',))
        idlist = preg.listPluginIds(IFoo)
        self.assertEqual(idlist,
                         ('bar_plugin', 'baz_plugin', 'foo_plugin'))

        # Moving the top plugin and another one could change something.
        preg.movePluginsUp(IFoo, ('bar_plugin', 'foo_plugin'))
        idlist = preg.listPluginIds(IFoo)
        self.assertEqual(idlist,
                         ('bar_plugin', 'foo_plugin', 'baz_plugin'))


    def test_movePluginsDown(self):
        from zope.interface import directlyProvides
        plugin_info, IFoo, IBar = self._makePluginInfo()
        parent = DummyFolder()
        foo_plugin = DummyPlugin()
        directlyProvides(foo_plugin, (IFoo,))
        parent._setObject('foo_plugin', foo_plugin)

        bar_plugin = DummyPlugin()
        directlyProvides(bar_plugin, (IFoo,))
        parent._setObject('bar_plugin', bar_plugin)

        baz_plugin = DummyPlugin()
        directlyProvides(baz_plugin, (IFoo,))
        parent._setObject('baz_plugin', baz_plugin)

        preg = self._makeOne(plugin_info).__of__(parent)

        preg.activatePlugin(IFoo, 'foo_plugin')
        preg.activatePlugin(IFoo, 'bar_plugin')
        preg.activatePlugin(IFoo, 'baz_plugin')

        self.assertRaises(ValueError, preg.movePluginsDown
                         , IFoo, ('quux_plugin',))

        preg.movePluginsDown(IFoo, ('foo_plugin', 'bar_plugin'))

        idlist = preg.listPluginIds(IFoo)
        self.assertEqual(len(idlist), 3)

        self.assertEqual(idlist[0], 'baz_plugin')
        self.assertEqual(idlist[1], 'foo_plugin')
        self.assertEqual(idlist[2], 'bar_plugin')

        # Moving the lowest plugin down should not change anything.
        preg.movePluginsDown(IFoo, ('bar_plugin',))
        idlist = preg.listPluginIds(IFoo)
        self.assertEqual(idlist,
                         ('baz_plugin', 'foo_plugin', 'bar_plugin'))

        # Moving the lowest plugin and another one could change something.
        preg.movePluginsDown(IFoo, ('bar_plugin', 'baz_plugin'))
        idlist = preg.listPluginIds(IFoo)
        self.assertEqual(idlist,
                         ('foo_plugin', 'baz_plugin', 'bar_plugin'))

    def test_getAllPlugins(self):
        from zope.interface import directlyProvides
        plugin_info, IFoo, IBar = self._makePluginInfo()
        parent = DummyFolder()
        foo_plugin = DummyPlugin()
        directlyProvides(foo_plugin, (IFoo,))
        parent._setObject('foo_plugin', foo_plugin)

        bar_plugin = DummyPlugin()
        directlyProvides(bar_plugin, (IFoo,))
        parent._setObject('bar_plugin', bar_plugin)

        baz_plugin = DummyPlugin()
        directlyProvides(baz_plugin, (IFoo,))
        parent._setObject('baz_plugin', baz_plugin)

        preg = self._makeOne(plugin_info).__of__(parent)

        first = preg.getAllPlugins('IFoo')

        self.assertEqual(len(first['active']), 0)

        self.assertEqual(len(first['available']), 3)
        self.failUnless('foo_plugin' in first['available'])
        self.failUnless('bar_plugin' in first['available'])
        self.failUnless('baz_plugin' in first['available'])

        preg.activatePlugin(IFoo, 'foo_plugin')

        second = preg.getAllPlugins('IFoo')

        self.assertEqual(len(second['active']), 1)
        self.failUnless('foo_plugin' in second['active'])

        self.assertEqual(len(second['available']), 2)
        self.failIf('foo_plugin' in second['available'])
        self.failUnless('bar_plugin' in second['available'])
        self.failUnless('baz_plugin' in second['available'])

        preg.activatePlugin(IFoo, 'bar_plugin')
        preg.activatePlugin(IFoo, 'baz_plugin')

        third = preg.getAllPlugins('IFoo')

        self.assertEqual(len(third['active']), 3)
        self.failUnless('foo_plugin' in third['active'])
        self.failUnless('bar_plugin' in third['active'])
        self.failUnless('baz_plugin' in third['active'])

        self.assertEqual(len(third['available']), 0)

    def test_removePluginById(self):
        from zope.interface import directlyProvides
        plugin_info, IFoo, IBar = self._makePluginInfo()
        parent = DummyFolder()
        foo_plugin = DummyPlugin()
        directlyProvides(foo_plugin, (IFoo, IBar))
        parent._setObject('foo_plugin', foo_plugin)

        bar_plugin = DummyPlugin()
        directlyProvides(bar_plugin, (IFoo,))
        parent._setObject('bar_plugin', bar_plugin)

        baz_plugin = DummyPlugin()
        directlyProvides(baz_plugin, (IBar,))
        parent._setObject('baz_plugin', baz_plugin)

        preg = self._makeOne(plugin_info).__of__(parent)

        preg.activatePlugin(IFoo, 'foo_plugin')
        preg.activatePlugin(IBar, 'foo_plugin')
        preg.activatePlugin(IFoo, 'bar_plugin')
        preg.activatePlugin(IBar, 'baz_plugin')

        preg.removePluginById('foo_plugin')

        idlist = preg.listPluginIds(IFoo)
        self.assertEqual(len(idlist), 1)
        self.assertEqual(idlist[0], 'bar_plugin')

        idlist = preg.listPluginIds(IBar)
        self.assertEqual(len(idlist), 1)
        self.assertEqual(idlist[0], 'baz_plugin')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(PluginRegistryTests),
    ))
