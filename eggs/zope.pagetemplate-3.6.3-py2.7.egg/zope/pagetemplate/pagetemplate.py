##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
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
"""Page Template module

HTML- and XML-based template objects using TAL, TALES, and METAL.
"""
import sys
from zope.tal.talparser import TALParser
from zope.tal.htmltalparser import HTMLTALParser
from zope.tal.talgenerator import TALGenerator
from zope.tal.talinterpreter import TALInterpreter
from zope.tales.engine import Engine
from zope.component import queryUtility

from zope.pagetemplate.interfaces import IPageTemplateSubclassing
from zope.pagetemplate.interfaces import IPageTemplateEngine
from zope.pagetemplate.interfaces import IPageTemplateProgram
from zope.interface import implements
from zope.interface import classProvides

_default_options = {}
_error_start = '<!-- Page Template Diagnostics'


class StringIO(list):
    """Unicode aware append-only version of StringIO.
    """
    write = list.append

    def __init__(self, value=None):
        list.__init__(self)
        if value is not None:
            self.append(value)

    def getvalue(self):
        return u''.join(self)


class PageTemplate(object):
    """Page Templates using TAL, TALES, and METAL.

    Subclassing
    -----------

    The following methods have certain internal responsibilities.

    pt_getContext(**keywords)
        Should ignore keyword arguments that it doesn't care about,
        and construct the namespace passed to the TALES expression
        engine.  This method is free to use the keyword arguments it
        receives.

    pt_render(namespace, source=False, sourceAnnotations=False, showtal=False)
        Responsible the TAL interpreter to perform the rendering.  The
        namespace argument is a mapping which defines the top-level
        namespaces passed to the TALES expression engine.

    __call__(*args, **keywords)
        Calls pt_getContext() to construct the top-level namespace
        passed to the TALES expression engine, then calls pt_render()
        to perform the rendering.
    """

    implements(IPageTemplateSubclassing)

    content_type = 'text/html'
    expand = 1
    _v_errors = ()
    _v_cooked = 0
    _v_macros = None
    _v_program = None
    _text = ''

    def macros(self):
        self._cook_check()
        return self._v_macros

    macros = property(macros)

    def pt_edit(self, text, content_type):
        if content_type:
            self.content_type = str(content_type)
        if hasattr(text, 'read'):
            text = text.read()
        self.write(text)

    def pt_getContext(self, args=(), options=_default_options, **ignored):
        rval = {'template': self,
                'options': options,
                'args': args,
                'nothing': None,
                }
        rval.update(self.pt_getEngine().getBaseNames())
        return rval

    def __call__(self, *args, **kwargs):
        return self.pt_render(self.pt_getContext(args, kwargs))

    def pt_getEngineContext(self, namespace):
        return self.pt_getEngine().getContext(namespace)

    def pt_getEngine(self):
        return Engine

    def pt_render(self, namespace, source=False, sourceAnnotations=False,
                  showtal=False):
        """Render this Page Template"""
        self._cook_check()

        __traceback_supplement__ = (
            PageTemplateTracebackSupplement, self, namespace
            )

        if self._v_errors:
            raise PTRuntimeError(str(self._v_errors))

        context = self.pt_getEngineContext(namespace)

        return self._v_program(
            context, self._v_macros, tal=not source, showtal=showtal,
            strictinsert=0, sourceAnnotations=sourceAnnotations
            )

    def pt_errors(self, namespace):
        self._cook_check()
        err = self._v_errors
        if err:
            return err
        try:
            self.pt_render(namespace, source=1)
        except:
            return ('Macro expansion failed', '%s: %s' % sys.exc_info()[:2])

    def write(self, text):
        # We accept both, since the text can either come from a file (and the
        # parser will take care of the encoding) or from a TTW template, in
        # which case we already have unicode.
        assert isinstance(text, (str, unicode))

        if text.startswith(_error_start):
            errend = text.find('-->')
            if errend >= 0:
                text = text[errend + 3:]
                if text[:1] == "\n":
                    text = text[1:]
        if self._text != text:
            self._text = text

        # Always cook on an update, even if the source is the same;
        # the content-type might have changed.
        self._cook()

    def read(self, request=None):
        """Gets the source, sometimes with macros expanded."""
        self._cook_check()
        if not self._v_errors:
            if not self.expand:
                return self._text
            try:
                # This gets called, if macro expansion is turned on.
                # Note that an empty dictionary is fine for the context at
                # this point, since we are not evaluating the template.
                context = self.pt_getContext(self, request)
                return self.pt_render(context, source=1)
            except:
                return ('%s\n Macro expansion failed\n %s\n-->\n%s' %
                        (_error_start, "%s: %s" % sys.exc_info()[:2],
                         self._text) )

        return ('%s\n %s\n-->\n%s' % (_error_start,
                                      '\n'.join(self._v_errors),
                                      self._text))

    def pt_source_file(self):
        """To be overridden."""
        return None

    def _cook_check(self):
        if not self._v_cooked:
            self._cook()

    def _cook(self):
        """Compile the TAL and METAL statments.

        Cooking must not fail due to compilation errors in templates.
        """

        pt_engine = self.pt_getEngine()
        source_file = self.pt_source_file()

        self._v_errors = ()

        try:
            engine = queryUtility(
                IPageTemplateEngine, default=PageTemplateEngine
                )
            self._v_program, self._v_macros = engine.cook(
                source_file, self._text, pt_engine, self.content_type)
        except:
            etype, e = sys.exc_info()[:2]
            self._v_errors = [
                "Compilation failed",
                "%s.%s: %s" % (etype.__module__, etype.__name__, e)
                ]

        self._v_cooked = 1


class PTRuntimeError(RuntimeError):
    '''The Page Template has template errors that prevent it from rendering.'''
    pass


class PageTemplateEngine(object):
    """Page template engine that uses the TAL interpreter to render."""

    implements(IPageTemplateProgram)
    classProvides(IPageTemplateEngine)

    def __init__(self, program):
        self.program = program

    def __call__(self, context, macros, **options):
        output = StringIO(u'')
        interpreter = TALInterpreter(
            self.program, macros, context,
            stream=output, **options
            )
        interpreter()
        return output.getvalue()

    @classmethod
    def cook(cls, source_file, text, engine, content_type):
        if content_type == 'text/html':
            gen = TALGenerator(engine, xml=0, source_file=source_file)
            parser = HTMLTALParser(gen)
        else:
            gen = TALGenerator(engine, source_file=source_file)
            parser = TALParser(gen)

        parser.parseString(text)
        program, macros = parser.getCode()

        return cls(program), macros


class PageTemplateTracebackSupplement(object):
    #implements(ITracebackSupplement)

    def __init__(self, pt, namespace):
        self.manageable_object = pt
        self.warnings = []
        e = pt.pt_errors(namespace)
        if e:
            self.warnings.extend(e)
