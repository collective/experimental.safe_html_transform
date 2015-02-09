##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Expression engine configuration and registration.

Each expression engine can have its own expression types and base names.

$Id: engine.py 126816 2012-06-11 19:00:21Z tseaver $
"""
from zope.tales.tales import ExpressionEngine
from zope.tales.expressions import PathExpr
from zope.tales.expressions import StringExpr
from zope.tales.expressions import NotExpr
from zope.tales.expressions import DeferExpr
from zope.tales.expressions import LazyExpr
from zope.tales.expressions import SimpleModuleImporter
from zope.tales.pythonexpr import PythonExpr

def Engine():
    e = ExpressionEngine()
    reg = e.registerType
    for pt in PathExpr._default_type_names:
        reg(pt, PathExpr)
    reg('string', StringExpr)
    reg('python', PythonExpr)
    reg('not', NotExpr)
    reg('defer', DeferExpr)
    reg('lazy', LazyExpr)
    e.registerBaseName('modules', SimpleModuleImporter())
    return e

Engine = Engine()
