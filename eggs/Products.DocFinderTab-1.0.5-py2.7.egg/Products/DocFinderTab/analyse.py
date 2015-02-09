# Copyright (C) 2001-2003 by Dr. Dieter Maurer <dieter@handshake.de>
# D-66386 St. Ingbert, Eichendorffstr. 23, Germany
#
#			All Rights Reserved
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice and this permission
# notice appear in all copies, modified copies and in
# supporting documentation.
#
# Dieter Maurer DISCLAIMS ALL WARRANTIES WITH
# REGARD TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL Dieter Maurer
# BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL
# DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
# PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.
"""analyse object for methods (names, arguments, documentation) and
permissions."""

# Detail types
DETAIL_PROGRAMMER= 'programmer'
DETAIL_SCRIPTER= 'scripter'
DETAIL_WEB= 'web'

from Products.DocFinderTab.config import FILTER_ROLES   # DFT
from Products.DocFinderTab.config import FILTER_METHODS # DFT

from inspect import isclass, ismethod, \
     isfunction, ismethoddescriptor, \
     getmro, \
     getargspec, formatargspec, \
     getcomments
import re, types

from AccessControl.SecurityInfo import ClassSecurityInfo, \
     ACCESS_PUBLIC, ACCESS_PRIVATE, ACCESS_NONE
from Acquisition import aq_base, Implicit
from Acquisition import Acquired                # DFT
from ComputedAttribute import ComputedAttribute # DFT
from DateTime import DateTime                   # DFT

# DFT
simple_types = {types.StringType: 1, types.IntType: 1,
                types.LongType: 1, types.FloatType: 1,
                types.TupleType: 1, types.ListType: 1,
                types.DictType: 1, types.NoneType: 1}

try: simple_types[types.UnicodeType] = 1
except: pass
try: simple_types[types.BooleanType] = 1
except: pass
try: simple_types[types.ComplexType] = 1
except: pass
try: simple_types[set] = 1
except: pass
try: simple_types[frozenset] = 1
except: pass
try: simple_types[ComputedAttribute] = 1
except: pass

# DFT
try:
    from datetime import datetime, date, time, timedelta
except ImportError:
    pass
else:
    simple_types[datetime] = 1
    simple_types[date] = 1
    simple_types[time] = 1
    simple_types[timedelta] = 1

_marker = {}


class Doc(Implicit):
  '''determine the documentation of an object.

  The documentation is described by a 'Doc' instance.
  It maintains.

   path -- the physical path of the documented object or 'None'

   title -- the title of the documented object or ''

   obj -- the documented object

   classes -- a two level sequence structure:

     1. classes, the object is build from, in message resolution order (mro).

        each class is described by a 'ClassDoc' instance

     2. for each class, the attributes defined by the class

        each attribute is described by a 'AttributeDoc' instance.

  The documentation does not include instance level attributes
  (they are too many). However, it does provide
  summary information about access to unprotected attributes
  in the doc for the pseudo class '-- Instance --'.
  This information is not accurate, as the
  '__allow_access_to_unprotected__subobjects__'
  evaluation is not precise.
  '''

  _classDict= None

  _secInfo= ClassSecurityInfo()
  _secInfo.declarePublic(
    'ObjToDoc__', 'DocType__', 'DocMethodRe__', 'Path', 'Title',
    '__getitem__','__len__','tpValues', 'tpId',
    )

  def __init__(self, obj, detail_type=DETAIL_SCRIPTER, method_filter= None):
    # note info for presentation
    self._ObjToDoc__= obj
    self._DocType__= detail_type
    self._DocMethodRe__= method_filter
    # path -- either the path to 'obj' or its 'repr'
    try: path= '/'.join(obj.getPhysicalPath())
    except AttributeError: path= repr(obj)
    # work around for a bug in 'string.translate' (does not like empty string)
    if not path: path='/'
    self._Path= path
    # title -- either 'obj.title' or 'obj.Title' or ''
    try: title= aq_base(obj).title
    except AttributeError:
      try: title= aq_base(obj).Title # for CMF
      except AttributeError: title= ''
    self._Title= title
    # encode type
    t= detail_type
    if isinstance(t, basestring):
      if t == DETAIL_PROGRAMMER: t= 10
      elif t == DETAIL_WEB: t= -10
      else: t= 0

    # try to get a name
    name= None
    i= getattr(obj,'getId',None) or getattr(obj,'id',None) or getattr(obj,'__name__',None)
    if i is not None:
      if callable(i): i= i()
      name= i
    if name is None: name= '-- Doc --'

    # permanent members
    self._classes= []
    self._type= t
    self._name= name
    self._method_filter=  method_filter and re.compile(method_filter).match

    # temporary members
    self._obj= obj
    self._attributes= {}
    self._check= self._makeUnprotectedChecker()

    c= _getClass(obj)

    ic= ClassDoc('-- Instance --')
    ic._append(AttributeDoc('-- unprotected attributes --',self._attrRoles(),obj= obj))
    self._classes.append(ic)

    for cl in _getMro(c): self._analyseClass(cl)

    # delete temporaries
    del self._obj
    del self._attributes
    del self._check


  def ObjToDoc__(self): return self._ObjToDoc__
  def DocType__(self): return self._DocType__
  def DocMethodRe__(self): return self._DocMethodRe__
  def Path(self): return self._Path
  def Title(self): return self._Title


  def __getitem__(self,k):
    '''allow access by both integer as well as class names.'''
    if isinstance(k, int): return self._classes[k]
    if self._classDict is None:
      cd= self._classDict= {}
      for c in self._classes: cd[c._name]= c
    return self._classDict[k].__of__(self)


  def __len__(self):
    '''the length of the classes.'''
    return len(self._classes)


  def tpValues(self):
    '''tuple of classes for tree display.'''
    return [c.__of__(self) for c in self._classes]

  def tpId(self):
    return self._name


  def _analyseClass(self, c,
                    _omit= {'__doc__': None, '__module__': None,
                            '__allow_access_to_unprotected_subobjects__': None,
                            '__dict__': None,                   # DFT
                            '__weakref__': None,                # DFT
                            '__slots__': None,                  # DFT
                            '__slotnames__': None,              # DFT
                            '__implements__': None,             # DFT
                            '__implements_advice_data__': None, # DFT
                            '__implemented__': None,            # DFT
                            '__provides__': None,               # DFT
                            '__providedBy__': None,             # DFT
                            'showDocumentation': None,          # DFT
                            'analyseDocumentation': None,       # DFT
                            }.has_key,
                    _allow= {'__len__': None,
                            '__nonzero__': None,    # DFT
                            '__str__': None,
                            '__getitem__': None,
                            '__call__': None,
                            }.has_key,
                    ):
    '''analyse *c*.'''
    cd= ClassDoc(c.__name__, getattr(c,'__doc__',None),_getLoc(c),_getComment(c))
    attributes= self._attributes; seen= attributes.has_key
    check= self._check; o= self._obj; filter= self._method_filter

    for (k,v) in c.__dict__.items():
      if k[-9:] == '__roles__' or _omit(k): continue
      if seen(k): continue
      attributes[k]= None
      if self._type <= 5:
        if k[0] == '_' and not _allow(k): continue
      if filter and not filter(k): continue
      r= getattr(o,k+'__roles__', check(k,v))
      if self._type <= 0 and _isPrivat(r): continue
      # something interesting
      a= AttributeDoc(k,r,v,o)
      if self._type <= -5 and not a.Doc(): continue
      cd._append(a)

    if filter and not cd: return    # DFT
    cd._finish()
    self._classes.append(cd)


  def _makeUnprotectedChecker(self):
    roles= getattr(self._obj,'__roles__', ACCESS_PUBLIC)
    allow= getattr(self._obj,'__allow_access_to_unprotected_subobjects__', 0)
    if isinstance(allow, (int, bool)):
      if not allow: roles= ACCESS_PRIVATE
      def check(name, value, roles=roles): return roles
    elif isinstance(allow, dict):
      def check(name, value, allow=allow.get, roles=roles, priv= ACCESS_PRIVATE):
        if allow(name): return roles
        return priv
    else:
      def check(name, value, allow=allow, roles=roles, priv= ACCESS_PRIVATE):
        if allow(name, value): return roles
        return priv
    return check


  def _attrRoles(self):
    roles= getattr(self._obj,'__roles__', ACCESS_PUBLIC)
    allow= getattr(self._obj,'__allow_access_to_unprotected_subobjects__', 0)
    if isinstance(allow, (int, bool)):
      if not allow: roles= ACCESS_PRIVATE
    elif isinstance(allow, dict): roles= 'Restricted (Dict)'
    else: roles= 'Restricted (Func)'
    return roles

  # may be necessary for 'ZTUtils.Tree.TreeMaker'
  def tpId(self):
    return self._Path



Doc._secInfo.apply(Doc)


class ClassDoc(Implicit):
  """the documentation of a class.

  It consists of a 'Name', 'Doc', 'Module' and a list of attributes,
  that can also be accessed via the attribute name.
  """

  _secInfo= ClassSecurityInfo()
  _secInfo.declarePublic('__getitem__','__len__','tpValues', 'tpId',
                         'Name', 'Doc', 'Module','Comment', 'FullName',
                         )

  _AttrDict= None

  def __init__(self,name,doc=None,mod=None,comment=None):
    self._name= name
    self._doc= doc
    self._mod= mod
    self._attrs= []
    self._comment= comment

  def __getitem__(self,k):
    '''allow access by both integer as well as attr names.'''
    if isinstance(k, int): return self._attrs[k]
    if self._AttrDict is None:
      cd= self._AttrDict= {}
      for c in self._attrs: cd[c._name]= c
    return self._AttrDict[k].__of__(self)


  def __len__(self):
    '''the length of the classes.'''
    return len(self._attrs)


  def tpValues(self):
    '''tuple of attributes for tree display.'''
    return [a.__of__(self) for a in self._attrs]

  def tpId(self):
    '''use name as id.'''
    return self._name


  def Name(self):
    '''the class name.'''
    return self._name

  def Doc(self):
    '''the class doc.'''
    return self._doc

  def Module(self):
    '''the module the class is defined in.'''
    return self._mod

  def Comment(self):
    '''the comment preceeding the class.'''
    return self._comment

  def FullName(self):
    '''the full class name (to be used with 'showCodeFor').'''
    return '%s.%s' % (self.Module(),self.Name())


  def _append(self,attr):
    '''append *attr*.'''
    self._attrs.append(attr)


  def _finish(self):
    '''finish class definition.'''
    self._attrs.sort(lambda a1,a2, cmp=cmp: cmp(a1._name,a2._name))


ClassDoc._secInfo.apply(ClassDoc)



class AttributeDoc(Implicit):
  """the documentation of an attribute.

  It consists of a 'Name', 'Roles', 'Args', 'Doc' and 'Type'.
  """

  _secInfo= ClassSecurityInfo()
  _secInfo.declarePublic('tpValues', 'tpId',
                         'Name', 'Roles', 'Args', 'Doc', 'Type', 'DocOrType',
                         'Comment', 'Permission', 'FullName',
                         )

  _knownPermission= 0

  def __init__(self,name,roles,value= _marker, obj= None):
    arguments= doc= comment= type= ''
    if value is not _marker:
      # determine arguments and documentation, if possible
      try: arguments= _findArgSpec(value)
      except: pass
      try: doc= _getDoc(value)        # DFT
      except: pass
      # determine comment if possible
      comment= _getComment(value)
      type= _getType(value)

    try: roles= _getRoles(roles)    # DFT
    except: pass
    self._name= name
    self._roles= roles
    self._arguments= arguments
    self._doc= doc
    self._type= type
    self._obj= obj
    self._comment= comment

  def Name(self):
    '''the attribute name'''
    return self._name

  def Roles(self):
    '''the attribute roles'''
    return self._roles

  def Args(self):
    '''the attribute arguments'''
    return self._arguments

  def Doc(self):
    '''the attribute documentation'''
    return self._doc

  def Type(self):
    '''the attribute type'''
    return self._type

  def tpValues(self):
    return ()

  def tpId(self):
    '''use name as id.'''
    return self._name

  def DocOrType(self):
    '''either the Doc (prefered) or the Type.'''
    return self.Doc() or self.Type()

  def FullName(self):
    '''the full class name (to be used with 'showCodeFor').'''
    return '%s.%s' % (self.aq_inner.aq_parent.FullName(),self.Name())

  def Permission(self):
    '''return the permission protecting the attribute, 'None' if not directly protected.'''
    if self._knownPermission: return self._permission
    p= None
    if self._obj is not None:
      name= self._name
      if name[:3] == '-- ': name= ''
      p= _lookup(self._obj, name+'__roles__')
      if p is not None:
        try:
          p= p[1]._p[1:-11].replace('_',' ')
        except: p= '-- explicit --'
    self._permission= p; self._knownPermission= 1
    return p

  def Comment(self):
    '''the comment preceeding the attribute.'''
    return self._comment



AttributeDoc._secInfo.apply(AttributeDoc)


def _isPrivat(role):
  return role == ACCESS_PRIVATE or role is ACCESS_NONE


def _getLoc(c):
  '''return location (module) of class *c*.'''
  return getattr(c,'__module__',None)

def _getComment(obj):
  '''return comment preceeding *obj*.'''
  try: return getcomments(obj)
  except: return ''


def _getType(v):
  '''return a nice representation of the *v* type.'''
  tn= type(v).__name__
  if tn == 'instance':
    tn= '%s %s' % (v.__class__.__name__,tn)
  elif tn == 'instance method':
    tn= '%s %s' % (v.im_class.__name__,tn)
  return tn


def _getClass(obj):
  '''return the class of *obj*.'''
  m= {}
  if getattr(obj,'_klass',m) is not m:
    return obj._klass
  else:
    return obj.__class__


_MROCache= {}
def _getMro(class_):
  '''*class_* s method resolution order (cached).'''
  mro= _MROCache.get(class_)
  if mro is None:
    mro= _MROCache[class_]= getmro(class_)
  return mro


# DFT
def _getDoc(obj, simple_types=simple_types):
    '''return the docstring of *obj*.'''
    if obj is Acquired:
        return 'Acquisition.Acquired'
    if obj is None:
        return 'None'
    if isinstance(obj, DateTime):
        return 'DateTime'
    if simple_types.has_key(type(obj)) or not _isNonPrimitive(obj):
        return ''
    if isinstance(obj, (staticmethod, classmethod)):
        return obj.__get__(obj).__doc__
    if FILTER_METHODS:
        if isfunction(obj) or ismethod(obj) or ismethoddescriptor(obj):
            if not obj.__doc__: return 'method'
    return obj.__doc__


# DFT
def _getRoles(roles):
    '''return nice names for *roles*.'''
    if FILTER_ROLES:
        if roles is ACCESS_PUBLIC: roles= 'public'
        elif roles == ACCESS_PRIVATE: roles= 'private'
        elif roles is ACCESS_NONE: roles= 'none'
        else: roles= _filterRoles(roles)
    else:
        if roles is ACCESS_PUBLIC: roles= 'ACCESS_PUBLIC'
        elif roles == ACCESS_PRIVATE: roles= 'ACCESS_PRIVATE'
        elif roles is ACCESS_NONE: roles= 'ACCESS_NONE'
    return roles


# DFT
def _filterRoles(roles):
    '''filter out faux roles.'''
    if not isinstance(roles, (list, tuple)):
        return roles

    def fauxRole(role):
        return role.startswith('_') and role.endswith('_Permission')

    unique= {}
    for role in roles:
        if not fauxRole(role):
            unique[role]= 1
    roles= unique.keys()
    roles.sort()
    return '(%s)' % ', '.join(roles)


def _lookup(obj,key):
  '''emulate Pythons name lookup; return pair (class,attr) or 'None'.'''
  m= {}
  od= getattr(obj,'__dict__',m)
  v= od.get(key,m)
  if v is not m: return (obj,v)
  v= _lookupClassHierarchy(_getClass(obj),key,m)
  return v


def _lookupClassHierarchy(c,k,m):
  for cl in _getMro(c):
    v= cl.__dict__.get(k,m)
    if v is not m: return (cl,v)
  return None


def _id(self): return self

def _findArgSpec(maybeFunction):
  '''the argument specification for *maybeFunction* or an exception.'''
  if isclass(maybeFunction):
    maybeFunction= getattr(maybeFunction,'__init__',_id)
  if isinstance(maybeFunction, (staticmethod, classmethod)):  # DFT
    maybeFunction= maybeFunction.__get__(maybeFunction)
  if ismethod(maybeFunction):
    maybeFunction= maybeFunction.im_func
  return formatargspec(*getargspec(maybeFunction))[1:-1]    # DFT

try:
  from ZPublisher.BaseRequest import typeCheck
  _isNonPrimitive= typeCheck
except ImportError:
  def _isNonPrimitive(value): return 1

