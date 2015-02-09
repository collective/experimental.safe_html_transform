##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for ActionIconsTool module.

$Id: test_ActionIconsTool.py 110650 2010-04-08 15:30:52Z tseaver $
"""

import unittest
import Testing

from zope.interface.verify import verifyClass


class ActionIconToolTests(unittest.TestCase):

    def _makeOne( self, *args, **kw ):

        from Products.CMFActionIcons.ActionIconsTool import ActionIconsTool

        return ActionIconsTool( *args, **kw )

    def test_interfaces(self):
        from Products.CMFActionIcons.ActionIconsTool import ActionIconsTool
        from Products.CMFActionIcons.interfaces import IActionIconsTool

        verifyClass(IActionIconsTool, ActionIconsTool)

    def test_empty( self ):

        tool = self._makeOne()

        self.assertEqual( len( tool.listActionIcons() ), 0 )
        self.assertRaises( KeyError, tool.getActionIcon, 'foo', 'bar' )
        self.assertEqual( tool.queryActionIcon( 'foo', 'bar' ), None )
        self.assertEqual( tool.queryActionIcon( 'foo', 'bar', 'baz' ), 'baz' )
        self.assertRaises( KeyError, tool.removeActionIcon, 'foo', 'bar' )

    def test_addActionIcon( self ):

        tool = self._makeOne()

        tool.addActionIcon( 'foo', 'bar', 'qux' )

        icons = tool.listActionIcons()
        self.assertEqual( len( icons ), 1 )

        icon = icons[0]
        self.assertEqual( icon.getCategory(), 'foo' )
        self.assertEqual( icon.getActionId(), 'bar' )
        self.assertEqual( icon.getExpression(), 'qux' )
        self.assertEqual( icon.getIconURL(), 'qux' )

        self.assertRaises( KeyError, tool.getActionIcon, 'foo', 'baz' )
        self.assertEqual( tool.getActionIcon( 'foo', 'bar' ), 'qux' )
        self.assertEqual( tool.queryActionIcon( 'foo', 'bar' ), 'qux' )
        self.assertEqual( tool.queryActionIcon( 'foo', 'bar', 'baz' ), 'qux' )

    def test_addActionIcon_duplicate( self ):

        tool = self._makeOne()

        tool.addActionIcon( 'foo', 'bar', 'qux' )
        self.assertRaises( KeyError, tool.addActionIcon, 'foo', 'bar', 'qux' )

    def test_addActionIcon_multiple( self ):

        tool = self._makeOne()

        tool.addActionIcon( 'foo', 'bar', 'qux' )
        tool.addActionIcon( 'foo', 'baz', 'spam' )
        tool.addActionIcon( 'abc', 'def', 'ghi' )

        icons = tool.listActionIcons()
        self.assertEqual( len( icons ), 3 )

        icon = icons[0]
        self.assertEqual( icon.getCategory(), 'foo' )
        self.assertEqual( icon.getActionId(), 'bar' )
        self.assertEqual( icon.getExpression(), 'qux' )
        self.assertEqual( icon.getIconURL(), 'qux' )

        icon = icons[1]
        self.assertEqual( icon.getCategory(), 'foo' )
        self.assertEqual( icon.getActionId(), 'baz' )
        self.assertEqual( icon.getExpression(), 'spam' )
        self.assertEqual( icon.getIconURL(), 'spam' )

        icon = icons[2]
        self.assertEqual( icon.getCategory(), 'abc' )
        self.assertEqual( icon.getActionId(), 'def' )
        self.assertEqual( icon.getExpression(), 'ghi' )
        self.assertEqual( icon.getIconURL(), 'ghi' )

    def test_updateActionIcon( self ):

        tool = self._makeOne()

        tool.addActionIcon( 'foo', 'bar', 'qux' )

        self.assertEqual( tool.getActionIcon( 'foo', 'bar' ), 'qux' )
        self.assertEqual( tool.queryActionIcon( 'foo', 'bar' ), 'qux' )
        self.assertEqual( tool.queryActionIcon( 'foo', 'bar', 'baz' ), 'qux' )

        tool.updateActionIcon( 'foo', 'bar', 'bam' )

        self.assertEqual( tool.getActionIcon( 'foo', 'bar' ), 'bam' )
        self.assertEqual( tool.queryActionIcon( 'foo', 'bar' ), 'bam' )
        self.assertEqual( tool.queryActionIcon( 'foo', 'bar', 'baz' ), 'bam' )

    def test_updateActionIcon_emptyiconexpr( self ):

        # CMF Collector # 239

        tool = self._makeOne()
        tool.addActionIcon( 'foo', 'bar', 'qux' )
        tool.updateActionIcon( 'foo', 'bar', '' )
        tool.updateActionIcon( 'foo', 'bar', 'bam' )

        self.assertEqual( tool.getActionIcon( 'foo', 'bar' ), 'bam' )
        self.assertEqual( tool.queryActionIcon( 'foo', 'bar' ), 'bam' )
        self.assertEqual( tool.queryActionIcon( 'foo', 'bar', 'baz' ), 'bam' )

    def test_updateActionIcon_nonesuch( self ):

        tool = self._makeOne()
        self.assertRaises( KeyError
                         , tool.updateActionIcon, 'foo', 'baz', 'qux' )

    def test_removeActionIcon( self ):

        tool = self._makeOne()

        tool.addActionIcon( 'foo', 'bar', 'qux' )
        tool.addActionIcon( 'foo', 'baz', 'spam' )
        tool.addActionIcon( 'abc', 'def', 'ghi' )

        tool.removeActionIcon( 'foo', 'baz' )

        icons = tool.listActionIcons()
        self.assertEqual( len( icons ), 2 )

        icon = icons[0]
        self.assertEqual( icon.getCategory(), 'foo' )
        self.assertEqual( icon.getActionId(), 'bar' )
        self.assertEqual( icon.getExpression(), 'qux' )
        self.assertEqual( icon.getIconURL(), 'qux' )

        icon = icons[1]
        self.assertEqual( icon.getCategory(), 'abc' )
        self.assertEqual( icon.getActionId(), 'def' )
        self.assertEqual( icon.getExpression(), 'ghi' )
        self.assertEqual( icon.getIconURL(), 'ghi' )

        self.assertEqual( tool.getActionIcon( 'foo', 'bar' ), 'qux' )
        self.assertRaises( KeyError, tool.getActionIcon, 'foo', 'baz' )
        self.assertEqual( tool.getActionIcon( 'abc', 'def' ), 'ghi' )

    def test_removeActionIcon_nonesuch( self ):

        tool = self._makeOne()

        tool.addActionIcon( 'foo', 'bar', 'qux' )
        tool.addActionIcon( 'foo', 'baz', 'spam' )
        tool.addActionIcon( 'abc', 'def', 'ghi' )

        self.assertRaises( KeyError, tool.removeActionIcon, 'jkl', 'mno' )

    def test_removeActionIcon_noIconURL( self ):
        # Regression test, issue #333
        tool = self._makeOne()
        tool.addActionIcon( 'foo', 'bar', '' )

        tool.removeActionIcon( 'foo', 'bar' )
        self.assertEqual(len(tool.listActionIcons()), 0)

    def test_updateActionDicts( self ):

        tool = self._makeOne()

        tool.addActionIcon( 'foo', 'bar', 'qux', 'FooBar' )
        tool.addActionIcon( 'foo', 'baz', 'spam', 'FooBaz', 1 )
        tool.addActionIcon( 'abc', 'def', 'ghi' )

        sod = { 'foo' : ( { 'id' : 'bar' }
                        , { 'id' : 'baz', 'icon' : 'qwerty' }
                        , { 'id' : 'bam' }
                        )
              , 'abc' : ( { 'id' : 'def', 'title' : 'DEF' }
                        ,
                        )
              }

        sod2 = tool.updateActionDicts( sod )

        self.assertEqual( len( sod2 ), len( sod ) )

        self.assertEqual( len( sod2['foo'] ), len( sod['foo'] ) )
        self.assertEqual( sod2['foo'][0]['icon'], 'qux' )
        self.assertEqual( sod2['foo'][0]['title'], 'FooBar' )
        self.assertEqual( sod2['foo'][0]['priority'], 0 )

        self.failIf( sod2['foo'][1].has_key( 'icon' ) ) # sorted higher!

        self.assertEqual( sod2['foo'][2]['icon'], 'spam' )
        self.assertEqual( sod2['foo'][2]['title'], 'FooBaz' )
        self.assertEqual( sod2['foo'][2]['priority'], 1 )

        self.assertEqual( len( sod2['abc'] ), len( sod['abc'] ) )
        self.assertEqual( sod2['abc'][0]['icon'], 'ghi' )
        self.assertEqual( sod2['abc'][0]['title'], 'DEF' )

        sod3 = tool( sod )
        self.assertEqual( sod2, sod3 )


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ActionIconToolTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
