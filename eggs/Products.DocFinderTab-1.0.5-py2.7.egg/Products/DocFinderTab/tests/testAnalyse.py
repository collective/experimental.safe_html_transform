#
# Test analyse
#

from Testing import ZopeTestCase

ZopeTestCase.installProduct('DocFinderTab')

from Products.DocFinderTab.analyse import DETAIL_PROGRAMMER
from Products.DocFinderTab.analyse import Doc

from Acquisition import Acquired, aq_base
from ComputedAttribute import ComputedAttribute
from OFS.SimpleItem import SimpleItem
from ExtensionClass import Base as ExtensionClass
from DateTime import DateTime

from datetime import datetime, date, time, timedelta

from inspect import ismethod, isfunction
from inspect import ismethoddescriptor, isdatadescriptor
from types import NoneType

import sys
PYTHON24 = sys.version_info >= (2, 4)
NEWSTYLE = issubclass(ExtensionClass, object)


def _func(self): pass

def _deco(func):
    def wrapper(self, *__args, **__kw):
        return func(self, *__args, **__kw)
    if PYTHON24:
        # __name__ is read-only in Python 2.3
        wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper

class Base(SimpleItem):
    def _basemethod(self): pass

class Foreign(SimpleItem):
    def _foreignmethod(self): pass

class Object(Base):

    _str = ''
    _int = 1
    _long = 1L
    _float = 1.0
    _tuple = ()
    _list = []
    _dict = {}
    _unicode = u''
    _bool = True
    _complex = 3.14j
    _none = None
    _DateTime = DateTime()
    _datetime = datetime.now()
    _date = date.today()
    _time = time(0, 0, 0)
    _timedelta = timedelta(seconds=1)

    if PYTHON24:
        _set = set([])
        _frozenset = frozenset([])

    _acquired = Acquired

    def __computed(self): pass
    _computed = ComputedAttribute(__computed)

    def __property_get(self): pass
    def __property_set(self, x): pass
    _property = property(__property_get, __property_set)

    def _method(self): pass
    _function = _func
    _basemethod = Base._basemethod
    _foreignmethod = Foreign._foreignmethod
    _basefunc = Base._basemethod.im_func
    _foreignfunc = Foreign._foreignmethod.im_func

    def __staticmethod(x): pass
    _staticmethod = staticmethod(__staticmethod)

    def __classmethod(cls, x): pass
    _classmethod = classmethod(__classmethod)

    _instance = Base()

    # Python 2.3 compatible decorator syntax
    def __decorated(self): pass
    _decorated = _deco(__decorated)

    # Python 2.3 compatible decorator syntax
    def __docdecorated(self):
        'decorated'
    _docdecorated = _deco(__docdecorated)

    def __init__(self, id):
        self.id = id

    def getitem(self, attr):
        return self.__class__.__dict__[attr]

    def getdoc(self, attr):
        doc = Doc(self, DETAIL_PROGRAMMER)
        for c in doc:
            if c.Name() == 'Object':
                for a in c:
                    if a.Name() == attr:
                        return a
        return None


class TestAnalyse(ZopeTestCase.ZopeTestCase):
    """ExtensionClass is a new-style class
    """

    def afterSetUp(self):
        self.folder._setObject('ob', Object('ob'))
        self.ob = self.folder.ob

    def testDummy(self):
        pass

    def testNewStyleClass(self):
        self.failUnless(issubclass(Object, object))

    def testNewStyleExtensionClass(self):
        self.failUnless(issubclass(ExtensionClass, object))

    def testStringType(self):
        self.failUnless(isinstance(self.ob._str, str))
        self.failUnless(isinstance(self.ob._str, basestring))
        self.assertEqual(self.ob.getdoc('_str').Type(), 'str')
        self.assertEqual(self.ob.getdoc('_str').Doc(), '')

    def testIntType(self):
        self.failUnless(isinstance(self.ob._int, int))
        self.failIf(isinstance(self.ob._int, long))
        self.assertEqual(self.ob.getdoc('_int').Type(), 'int')
        self.assertEqual(self.ob.getdoc('_int').Doc(), '')

    def testLongType(self):
        self.failUnless(isinstance(self.ob._long, long))
        self.failIf(isinstance(self.ob._long, int))
        self.assertEqual(self.ob.getdoc('_long').Type(), 'long')
        self.assertEqual(self.ob.getdoc('_long').Doc(), '')

    def testFloatType(self):
        self.failUnless(isinstance(self.ob._float, float))
        self.assertEqual(self.ob.getdoc('_float').Type(), 'float')
        self.assertEqual(self.ob.getdoc('_float').Doc(), '')

    def testListType(self):
        self.failUnless(isinstance(self.ob._list, list))
        self.assertEqual(self.ob.getdoc('_list').Type(), 'list')
        self.assertEqual(self.ob.getdoc('_list').Doc(), '')

    def testTupleType(self):
        self.failUnless(isinstance(self.ob._tuple, tuple))
        self.assertEqual(self.ob.getdoc('_tuple').Type(), 'tuple')
        self.assertEqual(self.ob.getdoc('_tuple').Doc(), '')

    def testDictType(self):
        self.failUnless(isinstance(self.ob._dict, dict))
        self.assertEqual(self.ob.getdoc('_dict').Type(), 'dict')
        self.assertEqual(self.ob.getdoc('_dict').Doc(), '')

    def testUnicodeType(self):
        self.failUnless(isinstance(self.ob._unicode, unicode))
        self.failUnless(isinstance(self.ob._unicode, basestring))
        self.assertEqual(self.ob.getdoc('_unicode').Type(), 'unicode')
        self.assertEqual(self.ob.getdoc('_unicode').Doc(), '')

    def testBooleanType(self):
        self.failUnless(isinstance(self.ob._bool, bool))
        self.failUnless(isinstance(self.ob._bool, int))
        self.assertEqual(self.ob.getdoc('_bool').Type(), 'bool')
        self.assertEqual(self.ob.getdoc('_bool').Doc(), '')

    def testComplexType(self):
        self.failUnless(isinstance(self.ob._complex, complex))
        self.assertEqual(self.ob.getdoc('_complex').Type(), 'complex')
        self.assertEqual(self.ob.getdoc('_complex').Doc(), '')

    def testNoneType(self):
        self.failUnless(isinstance(self.ob._none, NoneType))
        self.assertEqual(self.ob.getdoc('_none').Type(), 'NoneType')
        self.assertEqual(self.ob.getdoc('_none').Doc(), 'None')

    def testDateTime(self):
        self.failUnless(isinstance(self.ob._DateTime, DateTime))
        self.assertEqual(self.ob.getdoc('_DateTime').Type(), 'DateTime')
        self.assertEqual(self.ob.getdoc('_DateTime').Doc(), 'DateTime')

    def test_datetime(self):
        self.failUnless(isinstance(self.ob._datetime, datetime))
        self.assertEqual(self.ob.getdoc('_datetime').Type(), 'datetime')
        self.assertEqual(self.ob.getdoc('_datetime').Doc(), '')

    def test_date(self):
        self.failUnless(isinstance(self.ob._date, date))
        self.assertEqual(self.ob.getdoc('_date').Type(), 'date')
        self.assertEqual(self.ob.getdoc('_date').Doc(), '')

    def test_time(self):
        self.failUnless(isinstance(self.ob._time, time))
        self.assertEqual(self.ob.getdoc('_time').Type(), 'time')
        self.assertEqual(self.ob.getdoc('_time').Doc(), '')

    def test_timedelta(self):
        self.failUnless(isinstance(self.ob._timedelta, timedelta))
        self.assertEqual(self.ob.getdoc('_timedelta').Type(), 'timedelta')
        self.assertEqual(self.ob.getdoc('_timedelta').Doc(), '')

    if PYTHON24:
        def testSetType(self):
            self.failUnless(isinstance(self.ob._set, set))
            self.failIf(isinstance(self.ob._set, frozenset))
            self.assertEqual(self.ob.getdoc('_set').Type(), 'set')
            self.assertEqual(self.ob.getdoc('_set').Doc(), '')

        def testFrozenSetType(self):
            self.failUnless(isinstance(self.ob._frozenset, frozenset))
            self.failIf(isinstance(self.ob._frozenset, set))
            self.assertEqual(self.ob.getdoc('_frozenset').Type(), 'frozenset')
            self.assertEqual(self.ob.getdoc('_frozenset').Doc(), '')

    def testAcquiredType(self):
        # Acquisition.Acquired is a marker object and not a type!
        self.assertEqual(self.ob.getitem('_acquired'), Acquired)
        self.assertEqual(self.ob.getdoc('_acquired').Type(), 'str')
        self.assertEqual(self.ob.getdoc('_acquired').Doc(), 'Acquisition.Acquired')

    def testComputedAttributeType(self):
        self.assertEqual(type(self.ob.getitem('_computed')), ComputedAttribute)
        self.assertEqual(self.ob.getdoc('_computed').Type(), 'ComputedAttribute')
        self.assertEqual(self.ob.getdoc('_computed').Doc(), '')

    def testPropertyType(self):
        self.failUnless(isinstance(self.ob.getitem('_property'), property))
        self.failUnless(isdatadescriptor(self.ob.getitem('_property')))
        self.assertEqual(self.ob.getdoc('_property').Type(), 'property')
        self.assertEqual(self.ob.getdoc('_property').Doc(), None)
        #item = self.ob.getitem('_property')
        #print dir(item)
        #print item.fget, item.fset, item.fdel, item.__doc__

    def testMethodType(self):
        self.failUnless(ismethod(self.ob._method))
        self.assertEqual(type(self.ob._method).__name__, 'instancemethod')

        self.failUnless(isfunction(self.ob.getitem('_method')))
        self.assertEqual(type(self.ob.getitem('_method')).__name__, 'function')

        self.assertEqual(self.ob.getdoc('_method').Type(), 'function')
        self.assertEqual(self.ob.getdoc('_method').Doc(), 'method')

    def testFunctionType(self):
        self.failUnless(ismethod(self.ob._function))
        self.assertEqual(type(self.ob._function).__name__, 'instancemethod')

        self.failUnless(isfunction(self.ob.getitem('_function')))
        self.assertEqual(type(self.ob.getitem('_function')).__name__, 'function')

        self.assertEqual(self.ob.getdoc('_method').Type(), 'function')
        self.assertEqual(self.ob.getdoc('_method').Doc(), 'method')

    def testBaseMethodType(self):
        self.failUnless(ismethod(self.ob._basemethod))
        self.assertEqual(type(self.ob._basemethod).__name__, 'instancemethod')

        self.failUnless(ismethod(self.ob.getitem('_basemethod')))
        self.assertEqual(type(self.ob.getitem('_basemethod')).__name__, 'instancemethod')

        self.assertEqual(self.ob.getdoc('_basemethod').Type(), 'instancemethod')
        self.assertEqual(self.ob.getdoc('_basemethod').Doc(), 'method')

    def testBaseFuncType(self):
        self.failUnless(ismethod(self.ob._basefunc))
        self.assertEqual(type(self.ob._basefunc).__name__, 'instancemethod')

        self.failUnless(isfunction(self.ob.getitem('_basefunc')))
        self.assertEqual(type(self.ob.getitem('_basefunc')).__name__, 'function')

        self.assertEqual(self.ob.getdoc('_basefunc').Type(), 'function')
        self.assertEqual(self.ob.getdoc('_basefunc').Doc(), 'method')

    def testForeignMethodType(self):
        self.failUnless(ismethod(self.ob._foreignmethod))
        self.assertEqual(type(self.ob._foreignmethod).__name__, 'instancemethod')

        self.failUnless(ismethod(self.ob.getitem('_foreignmethod')))
        self.assertEqual(type(self.ob.getitem('_foreignmethod')).__name__, 'instancemethod')

        self.assertEqual(self.ob.getdoc('_foreignmethod').Type(), 'instancemethod')
        self.assertEqual(self.ob.getdoc('_foreignmethod').Doc(), 'method')

    def testForeignFuncType(self):
        self.failUnless(ismethod(self.ob._foreignfunc))
        self.assertEqual(type(self.ob._foreignfunc).__name__, 'instancemethod')

        self.failUnless(isfunction(self.ob.getitem('_foreignfunc')))
        self.assertEqual(type(self.ob.getitem('_foreignfunc')).__name__, 'function')

        self.assertEqual(self.ob.getdoc('_foreignfunc').Type(), 'function')
        self.assertEqual(self.ob.getdoc('_foreignfunc').Doc(), 'method')

    def testStaticMethodType(self):
        self.failUnless(isfunction(self.ob._staticmethod))
        self.assertEqual(type(self.ob._staticmethod).__name__, 'function')

        self.failUnless(ismethoddescriptor(self.ob.getitem('_staticmethod')))
        self.failUnless(isinstance(self.ob.getitem('_staticmethod'), staticmethod))
        self.assertEqual(type(self.ob.getitem('_staticmethod')).__name__, 'staticmethod')

        self.assertEqual(self.ob.getdoc('_staticmethod').Type(), 'staticmethod')
        self.assertEqual(self.ob.getdoc('_staticmethod').Doc(), None)
        #item = self.ob.getitem('_staticmethod')
        #print dir(item)
        #print item.__get__(item).__name__

    def testClassMethodType(self):
        self.failUnless(ismethod(self.ob._classmethod))
        self.assertEqual(type(self.ob._classmethod).__name__, 'instancemethod')

        self.failUnless(ismethoddescriptor(self.ob.getitem('_classmethod')))
        self.failUnless(isinstance(self.ob.getitem('_classmethod'), classmethod))
        self.assertEqual(type(self.ob.getitem('_classmethod')).__name__, 'classmethod')

        self.assertEqual(self.ob.getdoc('_classmethod').Type(), 'classmethod')
        self.assertEqual(self.ob.getdoc('_classmethod').Doc(), None)
        #item = self.ob.getitem('_classmethod')
        #print dir(item)
        #print item.__get__(item).__name__

    def testInstanceType(self):
        self.failUnless(isinstance(self.ob._instance, Base))
        self.assertEqual(self.ob.getdoc('_instance').Type(), 'Base')
        #self.assertEqual(self.ob.getdoc('_instance').Doc(), None)

    def testDecoratedType(self):
        self.failUnless(ismethod(self.ob._decorated))
        self.assertEqual(type(self.ob._decorated).__name__, 'instancemethod')

        self.failUnless(isfunction(self.ob.getitem('_decorated')))
        self.assertEqual(type(self.ob.getitem('_decorated')).__name__, 'function')

        self.assertEqual(self.ob.getdoc('_decorated').Type(), 'function')
        self.assertEqual(self.ob.getdoc('_decorated').Doc(), 'method')

    def testDocDecoratedType(self):
        self.failUnless(ismethod(self.ob._docdecorated))
        self.assertEqual(type(self.ob._docdecorated).__name__, 'instancemethod')

        self.failUnless(isfunction(self.ob.getitem('_docdecorated')))
        self.assertEqual(type(self.ob.getitem('_docdecorated')).__name__, 'function')

        self.assertEqual(self.ob.getdoc('_docdecorated').Type(), 'function')
        self.assertEqual(self.ob.getdoc('_docdecorated').Doc(), 'decorated')


class TestAnalyseClassic(TestAnalyse):
    """ExtensionClass is a classic class

       The method-ish types look slightly different. In fact, stuff like
       properties won't even work with classic classes.
    """

    def testNewStyleClass(self):
        self.failIf(issubclass(Object, object))

    def testNewStyleExtensionClass(self):
        self.failIf(issubclass(ExtensionClass, object))

    def testMethodType(self):
        self.failUnless(ismethod(self.ob._method))
        #self.assertEqual(type(self.ob._method).__name__, 'instancemethod')

        self.failUnless(isfunction(self.ob.getitem('_method')))
        self.assertEqual(type(self.ob.getitem('_method')).__name__, 'function')

        self.assertEqual(self.ob.getdoc('_method').Type(), 'function')
        self.assertEqual(self.ob.getdoc('_method').Doc(), 'method')

    def testFunctionType(self):
        self.failUnless(ismethod(self.ob._function))
        #self.assertEqual(type(self.ob._function).__name__, 'instancemethod')

        self.failUnless(isfunction(self.ob.getitem('_function')))
        self.assertEqual(type(self.ob.getitem('_function')).__name__, 'function')

        self.assertEqual(self.ob.getdoc('_method').Type(), 'function')
        self.assertEqual(self.ob.getdoc('_method').Doc(), 'method')

    def testBaseMethodType(self):
        self.failUnless(ismethod(self.ob._basemethod))
        #self.assertEqual(type(self.ob._basemethod).__name__, 'instancemethod')

        self.failUnless(ismethod(self.ob.getitem('_basemethod')))
        #self.assertEqual(type(self.ob.getitem('_basemethod')).__name__, 'instancemethod')

        #self.assertEqual(self.ob.getdoc('_basemethod').Type(), 'instancemethod')
        self.assertEqual(self.ob.getdoc('_basemethod').Doc(), 'method')

    def testBaseFuncType(self):
        self.failUnless(ismethod(self.ob._basefunc))
        #self.assertEqual(type(self.ob._basefunc).__name__, 'instancemethod')

        self.failUnless(isfunction(self.ob.getitem('_basefunc')))
        self.assertEqual(type(self.ob.getitem('_basefunc')).__name__, 'function')

        self.assertEqual(self.ob.getdoc('_basefunc').Type(), 'function')
        self.assertEqual(self.ob.getdoc('_basefunc').Doc(), 'method')

    def testForeignMethodType(self):
        self.failUnless(ismethod(self.ob._foreignmethod))
        #self.assertEqual(type(self.ob._foreignmethod).__name__, 'instancemethod')

        self.failUnless(ismethod(self.ob.getitem('_foreignmethod')))
        #self.assertEqual(type(self.ob.getitem('_foreignmethod')).__name__, 'instancemethod')

        #self.assertEqual(self.ob.getdoc('_foreignmethod').Type(), 'instancemethod')
        self.assertEqual(self.ob.getdoc('_foreignmethod').Doc(), 'method')

    def testForeignFuncType(self):
        self.failUnless(ismethod(self.ob._foreignfunc))
        #self.assertEqual(type(self.ob._foreignfunc).__name__, 'instancemethod')

        self.failUnless(isfunction(self.ob.getitem('_foreignfunc')))
        self.assertEqual(type(self.ob.getitem('_foreignfunc')).__name__, 'function')

        self.assertEqual(self.ob.getdoc('_foreignfunc').Type(), 'function')
        self.assertEqual(self.ob.getdoc('_foreignfunc').Doc(), 'method')

    def testStaticMethodType(self):
        #self.failUnless(isfunction(self.ob._staticmethod))
        #self.assertEqual(type(self.ob._staticmethod).__name__, 'function')

        self.failUnless(ismethoddescriptor(self.ob.getitem('_staticmethod')))
        self.failUnless(isinstance(self.ob.getitem('_staticmethod'), staticmethod))
        self.assertEqual(type(self.ob.getitem('_staticmethod')).__name__, 'staticmethod')

        self.assertEqual(self.ob.getdoc('_staticmethod').Type(), 'staticmethod')
        self.assertEqual(self.ob.getdoc('_staticmethod').Doc(), None)

    def testClassMethodType(self):
        #self.failUnless(ismethod(self.ob._classmethod))
        #self.assertEqual(type(self.ob._classmethod).__name__, 'instancemethod')

        self.failUnless(ismethoddescriptor(self.ob.getitem('_classmethod')))
        self.failUnless(isinstance(self.ob.getitem('_classmethod'), classmethod))
        self.assertEqual(type(self.ob.getitem('_classmethod')).__name__, 'classmethod')

        self.assertEqual(self.ob.getdoc('_classmethod').Type(), 'classmethod')
        self.assertEqual(self.ob.getdoc('_classmethod').Doc(), None)

    def testDecoratedType(self):
        self.failUnless(ismethod(self.ob._decorated))
        #self.assertEqual(type(self.ob._decorated).__name__, 'instancemethod')

        self.failUnless(isfunction(self.ob.getitem('_decorated')))
        self.assertEqual(type(self.ob.getitem('_decorated')).__name__, 'function')

        self.assertEqual(self.ob.getdoc('_decorated').Type(), 'function')
        self.assertEqual(self.ob.getdoc('_decorated').Doc(), 'method')

    def testDocDecoratedType(self):
        self.failUnless(ismethod(self.ob._docdecorated))
        #self.assertEqual(type(self.ob._docdecorated).__name__, 'instancemethod')

        self.failUnless(isfunction(self.ob.getitem('_docdecorated')))
        self.assertEqual(type(self.ob.getitem('_docdecorated')).__name__, 'function')

        self.assertEqual(self.ob.getdoc('_docdecorated').Type(), 'function')
        self.assertEqual(self.ob.getdoc('_docdecorated').Doc(), 'decorated')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    if NEWSTYLE:
        suite.addTest(makeSuite(TestAnalyse))
    else:
        suite.addTest(makeSuite(TestAnalyseClassic))
    return suite

