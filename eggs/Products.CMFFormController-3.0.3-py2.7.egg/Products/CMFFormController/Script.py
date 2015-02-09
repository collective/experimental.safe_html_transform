##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
# THIS FILE CONTAINS MODIFIED CODE FROM ZOPE 2.6.2
##############################################################################

import logging
import re

from App.class_init import InitializeClass
from Shared.DC.Scripts.Bindings import NameAssignments as BaseNameAssignments
from Products.PythonScripts.PythonScript import PythonScript as BasePythonScript
from Products.CMFCore.FSPythonScript import FSPythonScript as BaseFSPythonScript
from ZODB.POSException import ConflictError

logger = logging.getLogger('CMFFormController')

defaultBindings = {'name_context': 'context',
                   'name_container': 'container',
                   'name_m_self': 'script',
                   'name_ns': '',
                   'name_subpath': 'traverse_subpath',
                   'name_state': 'state'}

_nice_bind_names = {'context': 'name_context',
                    'container': 'name_container',
                    'script': 'name_m_self',
                    'namespace': 'name_ns',
                    'subpath': 'name_subpath',
                    'state': 'name_state'}

_first_indent = re.compile('(?m)^ *(?! |$)')
_nonempty_line = re.compile('(?m)^(.*\S.*)$')


class NameAssignments(BaseNameAssignments):
    _exprs = list(BaseNameAssignments._exprs)
    _exprs.append(('name_state', 'self._getState()'))
    _exprs = tuple(_exprs)


class PythonScript(BasePythonScript):

    def __init__(self, id, filepath=None):
        self.id = id
        self._filepath = filepath
        self.ZBindings_edit(defaultBindings)
        self._makeFunction()

    def _setupBindings(self, names={}):
        self._bind_names = names = NameAssignments(names)
        return names

    def _metadata_map(self):
        m = {
            'title': self.title,
            'parameters': self._params,
           }
        bindmap = self.getBindingAssignments().getAssignedNames()
        for k, v in _nice_bind_names.items():
            m['bind '+k] = bindmap.get(v, '')
        return m

    def write(self, text):
        """ Change the Script by parsing a read()-style source text. """
        self._validateProxy()
        mdata = self._metadata_map()
        bindmap = self.getBindingAssignments().getAssignedNames()
        bup = 0

        st = 0
        try:
            while 1:
                # Find the next non-empty line
                m = _nonempty_line.search(text, st)
                if not m:
                    # There were no non-empty body lines
                    body = ''
                    break
                line = m.group(0).strip()
                if line[:2] != '##':
                    # We have found the first line of the body
                    body = text[m.start(0):]
                    break

                st = m.end(0)
                # Parse this header line
                if len(line) == 2 or line[2] == ' ' or '=' not in line:
                    # Null header line
                    continue
                k, v = line[2:].split('=', 1)
                k = k.strip().lower()
                v = v.strip()
                if not mdata.has_key(k):
                    raise SyntaxError('Unrecognized header line "%s" in file %s' % (line, self._filepath))
                if v == mdata[k]:
                    # Unchanged value
                    continue

                # Set metadata value
                if k == 'title':
                    self.title = v
                elif k == 'parameters':
                    self._params = v
                elif k[:5] == 'bind ':
                    bindmap[_nice_bind_names[k[5:]]] = v
                    bup = 1

            body = body.rstrip()
            if body:
                body = body + '\n'
            if body != self._body:
                self._body = body
            if bup:
                self.ZBindings_edit(bindmap)
            else:
                self._makeFunction()
        except (ConflictError, KeyboardInterrupt):
            raise
        except:
            logger.exception('%s write failed' % self.meta_type)
            raise

InitializeClass(PythonScript)


class FSPythonScript(BaseFSPythonScript, PythonScript):
    def _createZODBClone(self):
        """Create a ZODB (editable) equivalent of this object."""
        obj = PythonScript(self.getId(), filepath=self._filepath)
        obj.write(self.read())
        return obj

    def __call__(self, *args, **kw):
        '''Calls the script.'''
        self._updateFromFS()
        return BaseFSPythonScript.__call__(self, *args, **kw)

    def _write(self, text, compile):
        '''
        Parses the source, storing the body, params, title, bindings,
        and source in self.  If compile is set, compiles the
        function.
        '''
        ps = PythonScript(self.id, filepath=self._filepath)
        ps.write(text)
        if compile:
            ps._makeFunction()
            self._v_ft = ps._v_ft
            self.func_code = ps.func_code
            self.func_defaults = ps.func_defaults
        self._body = ps._body
        self._params = ps._params
        self.title = ps.title
        self._setupBindings(ps.getBindingAssignments().getAssignedNames())
        self._source = ps.read()  # Find out what the script sees.

    def _metadata_map(self):
        m = {
            'title': self.title,
            'parameters': self._params,
           }
        bindmap = self.getBindingAssignments().getAssignedNames()
        for k, v in _nice_bind_names.items():
            m['bind '+k] = bindmap.get(v, '')
        return m

    _setupBindings = PythonScript._setupBindings
    _metadata_map = PythonScript._metadata_map
    write = PythonScript.write

InitializeClass(FSPythonScript)
