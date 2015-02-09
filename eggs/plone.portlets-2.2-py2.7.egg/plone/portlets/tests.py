import doctest
import unittest

import plone.portlets

from zope.component.testing import setUp, tearDown
from zope.configuration.xmlconfig import XMLConfig


optionflags = doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS


def configurationSetUp(test):
    setUp()

    import zope.browserpage
    import zope.component
    import zope.container
    import zope.contentprovider
    import zope.security

    XMLConfig('meta.zcml', zope.security)()
    XMLConfig('meta.zcml', zope.component)()
    XMLConfig('meta.zcml', zope.browserpage)()

    XMLConfig('configure.zcml', zope.component)()
    XMLConfig('configure.zcml', zope.security)()
    XMLConfig('configure.zcml', zope.container)()
    XMLConfig('configure.zcml', zope.contentprovider)()

    XMLConfig('configure.zcml', plone.portlets)()


def configurationTearDown(test):
    tearDown()


def test_safe_render():
    r"""
    Render the portlet safely, so that when an exception
    occurs, we log and don't bail out.

      >>> from plone.portlets.manager import PortletManagerRenderer
      >>> class PortletRenderer:
      ...     def __init__(self, error=False):
      ...         self.error = error
      ...     def render(self):
      ...         if self.error:
      ...             raise Exception()
      ...         return 'portlet rendered'

    When no error occurs, ``safe_render`` will return the portlet
    renderer's ``render()``:

      >>> renderer = PortletManagerRenderer(*(None,) * 4)
      >>> renderer.safe_render(PortletRenderer())
      'portlet rendered'

    When an error is raised, the ``error_message`` template is
    rendered:

      >>> renderer.error_message = lambda: 'error rendered'
      >>> renderer.safe_render(PortletRenderer(error=True))
      'error rendered'
    """


def test_portlet_metadata_availability():
    r"""
    Check that the __portlet_metadata__ field is available when
    the PortletManagerRenderer checks for the availability of
    the PortletRenderers

      >>> from zope.component import adapts
      >>> from zope.component import provideAdapter
      >>> from zope.interface import directlyProvides
      >>> from zope.interface import implements
      >>> from zope.interface import Interface

    Define a dummy PortletManager

      >>> from plone.portlets.interfaces import IPortletManager

      >>> class IDummyPortletManager(IPortletManager):
      ...     "Dummy portlet manager"

      >>> class DummyPortletManager:
      ...     implements(IDummyPortletManager)
      ...     __name__ = None

    Define a dummy PortletRenderer that is only available in case
    it has __portlet_metadata__

      >>> from plone.portlets.interfaces import IPortletRenderer
      >>> class DummyPortletRenderer:
      ...     implements(IPortletRenderer)
      ...
      ...     @property
      ...     def available(self):
      ...         return getattr(self, '__portlet_metadata__', False)
      ...
      ...     def render(self):
      ...         return u'dummy portlet renderer'
      ...
      ...     def update(self):
      ...         pass

    Define a dummy portlet retriever that adapts our dummy portlet manager
    and returns in its getPortlets a mock dictinary with a dummy
    PortletRenderer as p['assignment'].data. For that, we need a class
    where we can set an attribute 'data'

      >>> class Obj(object):
      ...     pass

      >>> from plone.portlets.constants import CONTEXT_CATEGORY
      >>> from plone.portlets.interfaces import IPortletRetriever
      >>> from plone.portlets.retriever import PortletRetriever

      >>> class DummyPortletRetriever(PortletRetriever):
      ...     implements(IPortletRetriever)
      ...     adapts(Interface, IDummyPortletManager)
      ...
      ...     def getPortlets(self):
      ...         p = dict()
      ...         p['category'] = CONTEXT_CATEGORY
      ...         p['key'] = p['name'] = u'dummy'
      ...         p['assignment'] = obj = Obj()
      ...         obj.data = DummyPortletRenderer()
      ...         obj.available = True
      ...         return (p, )

      >>> provideAdapter(DummyPortletRetriever)

    For instantiating a PortletManagerRenderer, we need a TestRequest

      >>> from zope.publisher.browser import TestRequest

    For our memoized views to work, we need to make the request annotatable

      >>> from zope.annotation.attribute import AttributeAnnotations
      >>> from zope.annotation.interfaces import IAttributeAnnotatable
      >>> from zope.interface import classImplements

      >>> classImplements(TestRequest, IAttributeAnnotatable)
      >>> provideAdapter(AttributeAnnotations)

    We need a dummy context that implements Interface

      >>> class DummyContext(object):
      ...     implements(Interface)

    We now test the PortletManagerRenderer. We override the _dataToPortlet
    method since our data is already our correct (dummy) IPortletRenderer

      >>> from plone.portlets.manager import PortletManagerRenderer
      >>> def _dataToPortlet(self, data):
      ...     return data
      >>> PortletManagerRenderer._dataToPortlet = _dataToPortlet

    Check that a PortletManagerRenderer is capable of rendering our
    dummy PortletRenderer

      >>> renderer = PortletManagerRenderer(DummyContext(),
      ...                                   TestRequest(),
      ...                                   None, DummyPortletManager())
      >>> renderer.update()
      >>> renderer.render()
      u'dummy portlet renderer'
    """


def test_suite():
    return unittest.TestSuite((
        doctest.DocFileSuite(
            'README.txt',
            setUp=configurationSetUp,
            tearDown=configurationTearDown,
            optionflags=optionflags),
        doctest.DocFileSuite(
            'uisupport.txt',
            setUp=configurationSetUp,
            tearDown=configurationTearDown,
            optionflags=optionflags),
        doctest.DocFileSuite(
            'utils.txt',
            setUp=configurationSetUp,
            tearDown=configurationTearDown,
            optionflags=optionflags),
        doctest.DocTestSuite()))
