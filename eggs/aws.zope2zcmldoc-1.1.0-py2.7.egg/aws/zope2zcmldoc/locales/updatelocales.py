# -*- coding: utf-8 -*-
# $Id: updatelocales.py 246082 2011-11-01 19:39:09Z glenfant $
"""\
i18n files maintenance utility. Please read the README.txt beside this
file.  Portions of this code have been stolen from
PlacelessTranslationService to prevent PYTHONPATH issues
"""
import os
import sys
import struct
import array
from cStringIO import StringIO
from stat import ST_MTIME

from i18ndude.script import rebuild_pot as i18n_rebuild_pot
from i18ndude.script import sync as i18n_sync

###
## START OF CUSTOMIZABLE SECTION
###

# Set this to True to get verbosity and keep temporary files if any
DEBUG = True

# Your main translation domain
DOMAIN = 'aws.zope2zcmldoc'

# Directories excluded from i18n markup search
EXCLUDED = ['tests']

###
## END OF CUSTOMIZABLE SECTION
###

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GENERATED_POT = '%s.pot' % DOMAIN
MANUAL_POT = '%s-manual.pot' % DOMAIN
if os.path.exists(MANUAL_POT):
    MERGE_OPT = ['--merge', MANUAL_POT]
else:
    MERGE_OPT = []
if EXCLUDED:
    EXCLUDED_OPT = '--exclude="%s"' % ' '.join(EXCLUDED)
else:
    EXCLUDED_OPT = ''
PO_FILENAME = '%s.po' % DOMAIN

def main():

    # Rebuilding the <domain>.pot
    if DEBUG:
        print "Rebuilding", GENERATED_POT
    argv = [
        'i18ndude', 'rebuild-pot',
        '--pot', GENERATED_POT,
        '--create', DOMAIN,
        MERGE_OPT,
        EXCLUDED_OPT,
        ROOT]
    sys.argv = flatten(argv)
    i18n_rebuild_pot()

    # Synching the .po files
    if DEBUG:
        print "Synching", PO_FILENAME, "files"
    argv = [
        'i18ndude', 'sync',
        '--pot', GENERATED_POT,
        find_po_files()
        ]
    sys.argv = flatten(argv)
    i18n_sync()

    # Compiling .po files
    if DEBUG:
        print "Compiling to", PO_FILENAME[:-2] + 'mo', "files"
    for po_filename in find_po_files():
        mo_filename = po_filename[:-2] + 'mo'
        if (not os.path.exists(mo_filename)
            or
            (os.stat(po_filename)[ST_MTIME] > os.stat(mo_filename)[ST_MTIME])):
            if DEBUG:
                print mo_filename
            po_hdl = file(mo_filename, 'wb')
            po_hdl.write(Msgfmt(po_filename).get())
            po_hdl.close()
    return

def flatten(seq):
    """
    >>> flatten([0, [1, 2, 3], [4, 5, [6, 7]]])
    [0, 1, 2, 3, 4, 5, 6, 7]
    """
    out = []
    for item in seq:
        if isinstance(item, (list, tuple)):
            out.extend(flatten(item))
        elif item:
            out.append(item)
    return out

def find_po_files():
    """List of abs paths to .po files"""
    po_files = []
    for root, dirs, files in os.walk(THIS_DIR):
        # Don' visit CSV or SVN marker dirs
        for blacklisted in ('CVS', '.svn'):
            if blacklisted in dirs:
                dirs.remove(blacklisted)
        if PO_FILENAME in files:
            po_files.append(os.path.join(root, PO_FILENAME))
    return po_files

###
## This part of the code has been stolen from PlacelessTranslationService
## to avoid PYTHONPATH headaches
###

class PoSyntaxError(Exception):
    """ Syntax error in a po file """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return 'Po file syntax error: %s' % self.msg

class Msgfmt(object):
    """Pythonic version of the GNU msgfmt command
    """
    def __init__(self, po, name='unknown'):
        self.po = po
        self.name = name
        self.messages = {}

    def readPoData(self):
        """ read po data from self.po and store it in self.poLines """
        output = []
        if isinstance(self.po, file):
            self.po.seek(0)
            output = self.po.readlines()
        if isinstance(self.po, list):
            output = self.po
        if isinstance(self.po, str):
            output = open(self.po, 'rb').readlines()
        if not output:
            raise ValueError, "self.po is invalid! %s" % type(self.po)
        return output

    def add(self, id, str, fuzzy):
        "Add a non-empty and non-fuzzy translation to the dictionary."
        if str and not fuzzy:
            self.messages[id] = str

    def generate(self):
        "Return the generated output."
        keys = self.messages.keys()
        # the keys are sorted in the .mo file
        keys.sort()
        offsets = []
        ids = strs = ''
        for id in keys:
            # For each string, we need size and file offset.  Each string is NUL
            # terminated; the NUL does not count into the size.
            offsets.append((len(ids), len(id), len(strs), len(self.messages[id])))
            ids += id + '\0'
            strs += self.messages[id] + '\0'
        output = ''
        # The header is 7 32-bit unsigned integers.  We don't use hash tables, so
        # the keys start right after the index tables.
        # translated string.
        keystart = 7*4+16*len(keys)
        # and the values start after the keys
        valuestart = keystart + len(ids)
        koffsets = []
        voffsets = []
        # The string table first has the list of keys, then the list of values.
        # Each entry has first the size of the string, then the file offset.
        for o1, l1, o2, l2 in offsets:
            koffsets += [l1, o1+keystart]
            voffsets += [l2, o2+valuestart]
        offsets = koffsets + voffsets
        output = struct.pack("Iiiiiii",
                             0x950412deL,       # Magic
                             0,                 # Version
                             len(keys),         # # of entries
                             7*4,               # start of key index
                             7*4+len(keys)*8,   # start of value index
                             0, 0)              # size and offset of hash table
        output += array.array("i", offsets).tostring()
        output += ids
        output += strs
        return output


    def get(self):
        """ """
        ID = 1
        STR = 2

        section = None
        fuzzy = 0

        lines = self.readPoData()

        # Parse the catalog
        lno = 0
        for l in lines:
            lno += 1
            # If we get a comment line after a msgstr or a line starting with
            # msgid, this is a new entry
            # XXX: l.startswith('msgid') is needed because not all msgid/msgstr
            # pairs in the plone pos have a leading comment
            if (l[0] == '#' or l.startswith('msgid')) and section == STR:
                self.add(msgid, msgstr, fuzzy)
                section = None
                fuzzy = 0
            # Record a fuzzy mark
            if l[:2] == '#,' and 'fuzzy' in l:
                fuzzy = 1
            # Skip comments
            if l[0] == '#':
                continue
            # Now we are in a msgid section, output previous section
            if l.startswith('msgid'):
                section = ID
                l = l[5:]
                msgid = msgstr = ''
            # Now we are in a msgstr section
            elif l.startswith('msgstr'):
                section = STR
                l = l[6:]
            # Skip empty lines
            l = l.strip()
            if not l:
                continue
            # XXX: Does this always follow Python escape semantics?
            # XXX: eval is evil because it could be abused
            try:
                l = eval(l, globals())
            except Exception, msg:
                raise PoSyntaxError('%s (line %d of po file %s): \n%s' % (msg, lno, self.name, l))
            if section == ID:
                msgid += l
            elif section == STR:
                msgstr += l
            else:
                raise PoSyntaxError('error in line %d of po file %s' % (lno, self.name))

        # Add last entry
        if section == STR:
            self.add(msgid, msgstr, fuzzy)

        # Compute output
        return self.generate()

    def getAsFile(self):
        return StringIO(self.get())

    def __call__(self):
        return self.getAsFile()

if __name__ == '__main__':
    main()
