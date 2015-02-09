=====================
Plone Portlets Engine
=====================

This package contains the basic interfaces and generalisable code for managing
dynamic portlets. Portlets are content providers (see ``zope.contentprovider``) 
which are assigned to columns or other areas (represented by portlet managers). 

The portlets infrastructure is similar to ``zope.viewlet``, but differs in that
lit is dynamic. Rather than register viewlets that "plug into" a viewlet manager
in ZCML, ``plone.portlets`` contains the basis for portlets that are assigned - 
persistently, at run time - to e.g. locations, content types, users or groups.

The remainder of this file will explain the API and components in detail, but
in general, the package is intended to be used as follows:

- The application layer registers a generic adapter to IPortletContext. Any
context where portlets may be assigned or displayed needs to be adaptable to 
this interface. It will inform the portlets infrastructure about things like
the parent of the current object (if any), and values for various categories
of portlets, such as the current user id for user portlets or a list of group
ids for group portlets.

- Any number of PortletManagers are stored persistently as local utilities. 
A PortletManager is a storage for site-wide portal assignments (e.g. user, 
group, content type). Contextual (location-specific) assignments are stored in 
annotations, on objects providing the ILocalPortletAssignable marker.

For example, there may be one portlet manager for the "left column" and one 
portlet manager for the "right column".

- When a PortletManager is registered as a local utility, an appropriate adapter
will also be registered (via an event handler) to support the 'provider:' TAL
expression. Thus, if the portlet manager is registered as a utility with name
'plone.leftcolumn'. Then, any template in that site would be able to write e.g. 
tal:replace="structure provider:plone.leftcolumn" to see the context-dependent 
rendering of that particular portlet manager. 

The rendering logic is found in an IPortletManagerRenderer, whilst the logic
of composing portlet registrations into a list of portlets to render, in a
particular order, is up to an IPortletRetriever.

Actual portlets are described by three interfaces, which may be kept separate or
implemented in the same component, depending on the use case.

- IPortletDataProvider is a marker interface for objects that provide 
configuration information for how a portlet should be rendered. This may be
an existing content object, or something specific to a portlet.

- A special type of content provider, IPortletRenderer, knows how to render each 
type of portlet. The IPortletRenderer should be a multi-adapter from 
(context, request, view, portlet manager, data provider).

- An IPortletAssignment is a persistent object that can be instantiated and
is stored by an IPortletManager or annotation on an ILocalPortletAssignable. 
The assignment is able to return an IPortletDataProvider to render.

Typically, you will either have a specific IPortletAssignment for a specific
IPortletDataProvider, or a generic IPortletAssignment for different types of
data providers. You will also typically have a generalisable IPortletRenderer 
for each type of data provider.

The examples below demonstrate a "specific-specific" portlet in the form of a 
login portlet - here, the same object provides both the assignment and the data 
provider aspect - and a "generic-generic" portlet, where a generic 
IPortletAssignment knows how to reference a content object, with different 
content objects potentially having different types of IPortletRenderers for 
rendering.

The portlet context
-------------------

We will create a test environment first, consisting of content objects (folders
and documents) that have a unique id managed by a global UID registry. For
the purposes of testing, we simply use the python id() for this, though this
is obviously not a realistic implementation (since it is non-persistent and
instance-specific). The environment also represents the current user and 
that user's groups.

  >>> from zope.interface import implements, Interface, directlyProvides
  >>> from zope.component import adapts, provideAdapter
  
  >>> from zope import schema
  
  >>> from zope.container.interfaces import IContained
  >>> from zope.site.interfaces import IFolder
  >>> from zope.site.folder import rootFolder, Folder
  
  >>> IFolder._content_iface = True
  
  >>> __uids__ = {}
  
  >>> class ITestUser(Interface):
  ...     id = schema.TextLine(title=u'User id')
  ...     groups = schema.Iterable(title=u'Groups of this user')
  
  >>> class ITestGroup(Interface):
  ...     id = schema.TextLine(title=u'Group id')
  
  >>> class TestUser(object):
  ...     implements(ITestUser)
  ...     def __init__(self, id, groups):
  ...         self.id = id
  ...         self.groups = groups
  
  >>> class TestGroup(object):
  ...     implements(ITestGroup)
  ...     def __init__(self, id):
  ...         self.id = id
  
  >>> Anonymous = TestUser('(Anonymous)', ())
  >>> user1 = TestUser('user1', (TestGroup('group1'), TestGroup('group2'),))
  >>> __current_user__ = user1
  
Now we can provide an IPortletContext for this environment. This allows the
portlets infrastructure to determine the parent of the current object (or at
least, the parent for portlet composition purposes). It also returns a list of
category -> key pairs.

Site-wide portlets are keyed to categories such as user, group, or content type.
The category can be any string, although these three have constants pre-defined
since they are likely to be the most useful ones. The portlet context informs
the IPortletRetriever which categories it should consider, and which keys (e.g.
user id, group id, content type name) to use to find the portlets that should be
shown in each category.

This retrieval of portlets from categories can either happen in "placeful" or 
"placeless mode", the difference being that placeful retrievals depend on the
specific context, whereas placeless retrievals do not. In this case, the
content-type category is placeless.

Also note that the order of the list returned matters - it will determine
the order in which portlets are rendered.

  >>> from plone.portlets.interfaces import IPortletContext
  >>> from plone.portlets.constants import USER_CATEGORY
  >>> from plone.portlets.constants import GROUP_CATEGORY
  >>> from plone.portlets.constants import CONTENT_TYPE_CATEGORY
  
  >>> class TestPortletContext(object):
  ...     implements(IPortletContext)
  ...     adapts(Interface)
  ...
  ...     def __init__(self, context):
  ...         self.context = context
  ...
  ...     @property
  ...     def uid(self):
  ...         return id(self.context)
  ...
  ...     def getParent(self):
  ...         return self.context.__parent__
  ...
  ...     def globalPortletCategories(self, placeless=False):
  ...         cats = []
  ...         if not placeless:
  ...             interfaces = self.context.__provides__.interfaces()
  ...             ct = [i for i in interfaces if
  ...                 getattr(i, '_content_iface', False)][0].getName()
  ...             cats.append((CONTENT_TYPE_CATEGORY, ct,))
  ...         cats.append((USER_CATEGORY, __current_user__.id,))
  ...         cats.extend([(GROUP_CATEGORY, i.id,) for i in __current_user__.groups])
  ...         return cats
  
  >>> provideAdapter(TestPortletContext)
  
We create the root of a sample content hierarchy as well, to be used later. We 
register new objects with our contrived UID registry, so that the generic 
portlet context will work for all of them.
  
  >>> class ITestDocument(IContained):
  ...     text = schema.TextLine(title=u"Text to render")
  >>> ITestDocument._content_iface = True
  
  >>> class TestDocument(object):
  ...     implements(ITestDocument)
  ...
  ...     def __init__(self, text=u''):
  ...         self.__name__ = None
  ...         self.__parent__ = None
  ...         self.text = text
  
  >>> rootFolder =  rootFolder()
  >>> __uids__[id(rootFolder)] = rootFolder
  
We then turn our root folder into a site, so that we can make local 
registrations on it.

  >>> from zope.location.interfaces import ISite
  >>> from zope.component.persistentregistry import PersistentComponents
  >>> from zope.component.globalregistry import base as siteManagerBase
  >>> from zope.component import getSiteManager
  
  >>> sm = PersistentComponents()
  >>> sm.__bases__ = (siteManagerBase,)
  >>> rootFolder.setSiteManager(sm)
  >>> ISite.providedBy(rootFolder)
  True
  
  >>> from zope.site.hooks import setSite, setHooks
  >>> setSite(rootFolder)
  >>> setHooks()
  
Registering portlet managers
----------------------------

Portlet managers are persistent objects that contain portlet assignments. They
are registered as utilities. When registered, an event handler will ensure that
an appropriate adapter is registered as well, to allow the  ``provider:`` TALES
expression to work.

  >>> from plone.portlets.interfaces import IPortletManager
  >>> from plone.portlets.manager import PortletManager
  
  >>> sm = getSiteManager(rootFolder)
  
  >>> sm.registerUtility(component=PortletManager(),
  ...                    provided=IPortletManager,
  ...                    name='columns.left')
  >>> sm.registerUtility(component=PortletManager(),
  ...                    provided=IPortletManager,
  ...                    name='columns.right')

  
We should now be able to get this via a provider: expression:

  >>> import os, tempfile
  >>> tempDir = tempfile.mkdtemp()
  >>> templateFileName = os.path.join(tempDir, 'template.pt')
  >>> open(templateFileName, 'w').write("""
  ... <html>
  ...   <body>
  ...     <div class="left-column">
  ...       <tal:block replace="structure provider:columns.left" />
  ...     </div>
  ...     <div class="right-column">
  ...       <tal:block replace="structure provider:columns.right" />
  ...     </div>
  ...   </body>
  ... </html>
  ... """)
  
We register the template as a view for all objects.

  >>> from zope.publisher.interfaces.browser import IBrowserPage
  >>> from zope.publisher.interfaces.browser import IBrowserRequest
  >>> from zope.publisher.browser import BrowserPage
  >>> from zope.browserpage import ViewPageTemplateFile
  >>> class TestPage(BrowserPage):
  ...     adapts(Interface, IBrowserRequest)
  ...     __call__ = ViewPageTemplateFile(templateFileName)
  >>> provideAdapter(TestPage, provides=IBrowserPage, name='main.html')

Then, we create a document that we can view.

  >>> doc1 = TestDocument()

We look up the view and render it. Note that the portlet manager is still empty
(no portlets have been assigned), so nothing will be displayed yet.

  >>> from zope.publisher.browser import TestRequest

For our memoised views to work, we need to make the request annotatable

  >>> from zope.annotation.interfaces import IAttributeAnnotatable
  >>> from zope.interface import classImplements
  >>> classImplements(TestRequest, IAttributeAnnotatable)

  >>> from zope.component import getMultiAdapter
  >>> view = getMultiAdapter((doc1, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
      </div>
      <div class="right-column">
      </div>
    </body>
  </html>
  
In fact, the renderer could've told us so:

  >>> from zope.publisher.interfaces.browser import IBrowserView
  >>> renderer = getMultiAdapter((doc1, TestRequest(), view), name='columns.left')
  >>> renderer.visible
  False
  
Creating portlets
-----------------

Portlets consist of a data provider (if necessary), a persistent assignment
object (that "instantiates" the portlet in a given portlet manager), and a
renderer. 

Recall from the beginning of this document that the relationship
between data providers and assignments are typically "specific-specific" or
"general-general". We will create a login box portlet as an example of a 
"specific-specific" portlet (where the assignment type is specific to the
portlet) and a portlet for showing the text of a TestDocument as defined above 
as an example of a "generic-generic" portlet (where the assignment type is 
generic for any content object in this test environment). Renderers are always
specific, of course - the way in which you render a document will be different
from the way you render an image.

Let's begin with the login portlet. Here, we keep the data provider and 
assignment aspects in the same object, since there is no need to reference an
external object.

  >>> from plone.portlets.interfaces import IPortletDataProvider
  >>> from plone.portlets.interfaces import IPortletAssignment
  >>> from plone.portlets.interfaces import IPortletRenderer
  >>> from plone.portlets.interfaces import IPortletManager
  >>> from persistent import Persistent
  >>> from zope.container.contained import Contained
  
  >>> class ILoginPortlet(IPortletDataProvider):
  ...   pass

  >>> class LoginPortletAssignment(Persistent, Contained):
  ...     implements(IPortletAssignment, ILoginPortlet)
  ...
  ...     @property
  ...     def available(self):
  ...         return __current_user__ is Anonymous
  ...
  ...     @property
  ...     def data(self):
  ...         return self
  
  >>> class LoginPortletRenderer(object):
  ...     implements(IPortletRenderer)
  ...     adapts(Interface, IBrowserRequest, IBrowserView, 
  ...             IPortletManager, ILoginPortlet)
  ... 
  ...     def __init__(self, context, request, view, manager, data):
  ...         self.data = data
  ...         self.available = True
  ...
  ...     def update(self):
  ...         pass
  ...
  ...     def render(self, *args, **kwargs):
  ...         return r'<form action="/login">(test)</form>'
  >>> provideAdapter(LoginPortletRenderer)
  
Note that in a real-world application, it may be necessary to add security
assertions to the LoginPortletAssignment class.
  
For the document-text portlet, we separate the data provider from the 
assignment object. We don't even use IPortletDataProvider in this case,
as the ITestContent interface is already available.

Notice that the assignment type is generic here, relying on the contrived UID
that the portlet context also relies upon.

  >>> class UIDPortletAssignment(Persistent, Contained):
  ...     implements(IPortletAssignment)
  ...     
  ...     def __init__(self, obj):
  ...         self.uid = id(obj)
  ...
  ...     @property
  ...     def available(self):
  ...         return True
  ...
  ...     @property
  ...     def data(self):
  ...          return __uids__[self.uid]
  
  >>> class DocumentPortletRenderer(object):
  ...     implements(IPortletRenderer)
  ...     adapts(Interface, IBrowserRequest, IBrowserView, 
  ...             IPortletManager, ITestDocument)
  ... 
  ...     def __init__(self, context, request, view, manager, data):
  ...         self.data = data
  ...         self.available = True
  ...
  ...     def update(self):
  ...         pass
  ...
  ...     def render(self, *args, **kwargs):
  ...         return r'<div>%s</div>' % (self.data.text,)
  >>> provideAdapter(DocumentPortletRenderer)

Assigning portlets to contexts
------------------------------

We can now assign portlets to different portlet managers (columns) in different
contexts, and they will be rendered in the view that references them, as defined 
above. Portlets can also be assigned to site-wide categories such as 
content-type, user, or group. We will see examples of those types of assignments
later.

Let's assign some portlets in the context of the root folder. Assignment is
done by adapting an ILocalPortletAssignable and the IPortletManager representing
a column to IPortletAssignmentMapping. ILocalPortletAssignable in turn is a 
marker interface that informs us that we can annotate the content object with 
the portlet assignments.

First, we get the portlet managers for the left and right columns.

  >>> from zope.component import getUtility
  >>> left = getUtility(IPortletManager, name='columns.left')
  >>> right = getUtility(IPortletManager, name='columns.right')
  
Then, let's mark Folder and TestDocument as being able to have local portlet 
assignments.

  >>> from plone.portlets.interfaces import ILocalPortletAssignable
  >>> from zope.interface import classImplements
  >>> classImplements(TestDocument, ILocalPortletAssignable)
  >>> classImplements(Folder, ILocalPortletAssignable)
  
  >>> from plone.portlets.interfaces import IPortletAssignmentMapping
  >>> lpa = LoginPortletAssignment()
  >>> leftAtRoot = getMultiAdapter((rootFolder, left), IPortletAssignmentMapping)
  
The IPortletAssignmentMapping is a container. In fact, we probably don't have
a meaningful name for a portlet assignment instance (and we don't much care,
so long as it is unique), so it provides the IContainerNamesContainer marker.
This will inform the adding view that it should use an INameChooser to pick
an appropriate name. We will simulate that here with the following function,
for convenience.

  >>> from zope.container.interfaces import INameChooser
  >>> def saveAssignment(mapping, assignment):
  ...     chooser = INameChooser(mapping)
  ...     mapping[chooser.chooseName('', assignment)] = assignment
  
  >>> saveAssignment(leftAtRoot, lpa)
  >>> lpa.__name__ in leftAtRoot
  True

Let's assign some more portlets. This time we will use a UID assignment to
reference two documents that will be rendered with an appropriate document
portlet renderer.
  
  >>> doc1 = TestDocument(u'Test document one')
  >>> __uids__[id(doc1)] = doc1
  >>> rootFolder['doc1'] = doc1
  >>> dpa1 = UIDPortletAssignment(doc1)
  
  >>> doc2 = TestDocument(u'Test document two')
  >>> __uids__[id(doc2)] = doc2
  >>> rootFolder['doc2'] = doc2
  >>> dpa2 = UIDPortletAssignment(doc2)
  
  >>> rightAtRoot = getMultiAdapter((rootFolder, right), IPortletAssignmentMapping)
  >>> saveAssignment(rightAtRoot, dpa2)
  >>> saveAssignment(rightAtRoot, dpa1)
  
We can also re-order assignments:

  >>> rightKeys = list(rightAtRoot.keys())
  >>> rightKeys = [rightKeys[1]] + [rightKeys[0]] + rightKeys[2:]
  >>> rightAtRoot.updateOrder(rightKeys)
  >>> rightAtRoot.values()[0] is dpa1
  True
  >>> rightAtRoot.values()[1] is dpa2
  True

If we now render the view, we should see our newly assigned portlets.

  >>> view = getMultiAdapter((rootFolder, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
      </div>
      <div class="right-column">
        <div>Test document one</div>
        <div>Test document two</div>
      </div>
    </body>
  </html>
  
Notice that the login portlet did not get rendered, since its 'available'
property was false (the current user is not the anonymous user). Let's
"log out" and verify that it show up.

  >>> __current_user__ = Anonymous
  >>> view = getMultiAdapter((rootFolder, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <form action="/login">(test)</form>
      </div>
      <div class="right-column">
        <div>Test document one</div>
        <div>Test document two</div>
      </div>
    </body>
  </html>
  
For the remainder of these tests, we will use a dummy portlet to make test
writing a bit easier:

  >>> class IDummyPortlet(IPortletDataProvider):
  ...   text = schema.TextLine(title=u'Text to render')
  
  >>> class DummyPortlet(Persistent, Contained):
  ...     implements(IPortletAssignment, IDummyPortlet)
  ...     
  ...     def __init__(self, text, available=True):
  ...         self.text = text
  ...         self.available = available
  ...     data = property(lambda self: self)
  
  >>> class DummyPortletRenderer(object):
  ...     implements(IPortletRenderer)
  ...     adapts(Interface, IBrowserRequest, IBrowserView, 
  ...             IPortletManager, IDummyPortlet)
  ... 
  ...     def __init__(self, context, request, view, manager, data):
  ...         self.data = data
  ...         self.available = True
  ...
  ...     def update(self):
  ...         pass
  ...
  ...     def render(self, *args, **kwargs):
  ...         return r'<div>%s</div>' % (self.data.text,)
  >>> provideAdapter(DummyPortletRenderer)
  
Let's assign a portlet in a sub-folder of the root folder.

  >>> child1 = Folder()
  >>> rootFolder['child1'] = child1
  >>> __uids__[id(child1)] = child1
  
  >>> childPortlet = DummyPortlet('Dummy at child1')
  >>> leftAtChild1 = getMultiAdapter((child1, left), IPortletAssignmentMapping)
  >>> saveAssignment(leftAtChild1, childPortlet)
  
This assignment does not affect rendering at the root folder:

  >>> view = getMultiAdapter((rootFolder, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <form action="/login">(test)</form>
      </div>
      <div class="right-column">
        <div>Test document one</div>
        <div>Test document two</div>
      </div>
    </body>
  </html>
  
It does, however, affect rendering at 'child1' (and any of its children).
Notice also that by default, child portlets come before parent portlets.

  >>> view = getMultiAdapter((child1, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
        <form action="/login">(test)</form>
      </div>
      <div class="right-column">
        <div>Test document one</div>
        <div>Test document two</div>
      </div>
    </body>
  </html>
  
Assigning portlets to site-wide categories
-------------------------------------------
  
We can now assign a portlet to a user. Notice how one user's portlets
don't interfere with those of another user, and that by default, user portlets
are listed after contextual portlets (in fact, the default IPortletRetriever
puts all site-wide portlets after contextual portlets).

In fact, the portlets machinery doesn't consider the 'user' category of
site-wide portlets any different from the 'group' or 'content_type' or 'foobar'
category. It simply looks up categories and keys in the appropriate portlet
manager. Notice how these correspond to those returned by our TestPortletContext
above, however.

Thus, we must first create the user category.

  >>> from plone.portlets.storage import PortletCategoryMapping
  >>> from plone.portlets.storage import PortletAssignmentMapping
  
Then we create assignment mappings for each user. These are very much like
the LocalPortletAssignmentManager we used to assign contextual portlets
above.

  >>> left[USER_CATEGORY] = PortletCategoryMapping()
  >>> left[USER_CATEGORY][Anonymous.id] = PortletAssignmentMapping()
  >>> left[USER_CATEGORY][user1.id] = PortletAssignmentMapping()
  
  >>> anonPortlet = DummyPortlet('Dummy for anonymous')
  >>> userPortlet = DummyPortlet('Dummy for user1')
  
  >>> saveAssignment(left[USER_CATEGORY][Anonymous.id], anonPortlet)
  >>> saveAssignment(left[USER_CATEGORY][user1.id], userPortlet)
  
These will now be rendered as expected.
  
  >>> view = getMultiAdapter((child1, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
        <form action="/login">(test)</form>
        <div>Dummy for anonymous</div>
      </div>
      <div class="right-column">
        <div>Test document one</div>
        <div>Test document two</div>
      </div>
    </body>
  </html>
  
  >>> __current_user__ = user1
  >>> view = getMultiAdapter((child1, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
        <div>Dummy for user1</div>
      </div>
      <div class="right-column">
        <div>Test document one</div>
        <div>Test document two</div>
      </div>
    </body>
  </html>
  
We can also assign portlets to groups. This is no different to assigning
portlets to users - we simply use a different category.

  >>> group1 = user1.groups[0]
  >>> group2 = user1.groups[1]
  
  >>> left[GROUP_CATEGORY] = PortletCategoryMapping()
  >>> left[GROUP_CATEGORY][group1.id] = PortletAssignmentMapping()
  >>> left[GROUP_CATEGORY][group2.id] = PortletAssignmentMapping()
  
  >>> groupPortlet1 = DummyPortlet('Dummy for group1')
  >>> groupPortlet2 = DummyPortlet('Dummy for group2')
  
  >>> saveAssignment(left[GROUP_CATEGORY][group1.id], groupPortlet1)
  >>> saveAssignment(left[GROUP_CATEGORY][group2.id], groupPortlet2)
  
  >>> view = getMultiAdapter((child1, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
        <div>Dummy for user1</div>
        <div>Dummy for group1</div>
        <div>Dummy for group2</div>
      </div>
      <div class="right-column">
        <div>Test document one</div>
        <div>Test document two</div>
      </div>
    </body>
  </html>
  
Blacklisting portlets
---------------------

It may not be desirable in all cases to inherit portlets like this. We can
blacklist specific categories, including the special 'context' category,
at a particular ILocalPortletAssignable, via an ILocalPortletAssignmentManager.

The blacklist status can be True (block this category), False (show this
category) or None (let the parent decide).

  >>> from plone.portlets.interfaces import ILocalPortletAssignmentManager
  >>> leftAtChild1Manager = getMultiAdapter((child1, left), ILocalPortletAssignmentManager)
  >>> leftAtChild1Manager.getBlacklistStatus(USER_CATEGORY) is None
  True
  >>> leftAtChild1Manager.setBlacklistStatus(USER_CATEGORY, True)
  >>> leftAtChild1Manager.getBlacklistStatus(USER_CATEGORY)
  True
  
  >>> view = getMultiAdapter((child1, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
        <div>Dummy for group1</div>
        <div>Dummy for group2</div>
      </div>
      <div class="right-column">
        <div>Test document one</div>
        <div>Test document two</div>
      </div>
    </body>
  </html>
  
The status is inherited from a parent unless a child also sets a status:

  >>> leftAtRootManager = getMultiAdapter((rootFolder, left), ILocalPortletAssignmentManager)
  >>> leftAtRootManager.setBlacklistStatus(GROUP_CATEGORY, True)
  >>> view = getMultiAdapter((child1, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
      </div>
      <div class="right-column">
        <div>Test document one</div>
        <div>Test document two</div>
      </div>
    </body>
  </html>
  
  >>> leftAtChild1Manager.setBlacklistStatus(GROUP_CATEGORY, False)
  >>> view = getMultiAdapter((child1, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
        <div>Dummy for group1</div>
        <div>Dummy for group2</div>
      </div>
      <div class="right-column">
        <div>Test document one</div>
        <div>Test document two</div>
      </div>
    </body>
  </html>
  
When setting the blacklist status of the 'context' category, assignments
at the particular context will still apply.

  >>> rightAtChild1Manager = getMultiAdapter((child1, right), ILocalPortletAssignmentManager)
  >>> from plone.portlets.constants import CONTEXT_CATEGORY
  >>> rightAtChild1Manager.setBlacklistStatus(CONTEXT_CATEGORY, True)
  >>> view = getMultiAdapter((child1, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
        <div>Dummy for group1</div>
        <div>Dummy for group2</div>
      </div>
      <div class="right-column">
      </div>
    </body>
  </html>
  
  >>> rightAtChild1 = getMultiAdapter((child1, right), IPortletAssignmentMapping)
  >>> saveAssignment(rightAtChild1, DummyPortlet('Dummy at child 1 right'))

  >>> view = getMultiAdapter((child1, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
        <div>Dummy for group1</div>
        <div>Dummy for group2</div>
      </div>
      <div class="right-column">
        <div>Dummy at child 1 right</div>
      </div>
    </body>
  </html>
  
If we create a child of child1, it will see that the portlets above child1
are still blocked, but those from child11 are not blocked.

  >>> child11 = Folder()
  >>> child1['child11'] = child11
  >>> __uids__[id(child11)] = child11
  
  >>> view = getMultiAdapter((child11, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
        <div>Dummy for group1</div>
        <div>Dummy for group2</div>
      </div>
      <div class="right-column">
        <div>Dummy at child 1 right</div>
      </div>
    </body>
  </html>
  
  >>> rightAtChild11 = getMultiAdapter((child11, right), IPortletAssignmentMapping)
  >>> saveAssignment(rightAtChild11, DummyPortlet('Dummy at child 11 right'))
  
  >>> view = getMultiAdapter((child11, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
        <div>Dummy for group1</div>
        <div>Dummy for group2</div>
      </div>
      <div class="right-column">
        <div>Dummy at child 11 right</div>
        <div>Dummy at child 1 right</div>
      </div>
    </body>
  </html>
  
We'd get the same effect by explicitly not blocking: if child11 had the 
context category to "always show" (white-listing), it will get the portlets 
from child1, but not those from the root folder. Thus, there is little
difference between the blocking states 'None' and 'False' for contextual
portlets. In the UI, a simple True/False or True/None may suffice.
  
  >>> rightAtChild11Manager = getMultiAdapter((child11, right), ILocalPortletAssignmentManager)
  >>> rightAtChild11Manager.setBlacklistStatus(CONTEXT_CATEGORY, False)
  >>> view = getMultiAdapter((child11, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
        <div>Dummy for group1</div>
        <div>Dummy for group2</div>
      </div>
      <div class="right-column">
        <div>Dummy at child 11 right</div>
        <div>Dummy at child 1 right</div>
      </div>
    </body>
  </html>
  
If we wanted to hide the parent portlets here as well, we could explicitly
block them as well.
  
  >>> rightAtChild11Manager = getMultiAdapter((child11, right), ILocalPortletAssignmentManager)  
  >>> rightAtChild11Manager.setBlacklistStatus(CONTEXT_CATEGORY, True)
  >>> view = getMultiAdapter((child11, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="left-column">
        <div>Dummy at child1</div>
        <div>Dummy for group1</div>
        <div>Dummy for group2</div>
      </div>
      <div class="right-column">
        <div>Dummy at child 11 right</div>
      </div>
    </body>
  </html>

Blocking parent contextual portlets by default
----------------------------------------------

To create a portlet manager that blocks parent contextual portlets by default
register an IBlockingPortletManager instead.

  >>> from plone.portlets.interfaces import IBlockingPortletManager 
  >>> from zope.interface import alsoProvides
  >>> alsoProvides(right, IBlockingPortletManager)

Parent contextual portlets are now blacklisted by default.

  >>> child2 = Folder()
  >>> child1['child2'] = child2
  >>> __uids__[id(child2)] = child2

  >>> rightAtChild2Manager = getMultiAdapter((child2, right), ILocalPortletAssignmentManager)
  >>> rightAtChild2Manager.getBlacklistStatus(CONTEXT_CATEGORY)
  True

And are hidden in the view.

  >>> view = getMultiAdapter((child2, TestRequest()), name='main.html')
  >>> print view().strip()
    <html>
      <body>
        <div class="left-column">
          <div>Dummy at child1</div>
          <div>Dummy for group1</div>
          <div>Dummy for group2</div>
        </div>
        <div class="right-column">
        </div>
      </body>
    </html>

Using a different retrieval algorithm
-------------------------------------

The examples above show the default portlet retrival algorithm, which finds
portlets for children before those for parents before those for users
before those for groups. It is relatively easy to plug in different composition
algorithm, however.

Consider the case of a "dashboard" where a user can assign personal portlets.
This may be a special page that is not context-dependent, considering only
user and group portlets.

The portlet manager renderer will adapt its context and the portlet manager to 
an IPortletRetreiver in order to get a list of portlets to display. 
plone.portlets ships with an alternative version of the default 
IPortletRetriever that ignores contextual portlets. This is registered as an 
adapter from (Interface, IPlacelessPortletManager). IPlacelessPortletManager in
turn, is a marker interface that you can apply to a portlet manager to get the 
placeless behaviour.

  >>> from plone.portlets.interfaces import IPlacelessPortletManager
  
  >>> sm = getSiteManager(rootFolder)
  >>> dashboardPortletManager = PortletManager()
  >>> directlyProvides(dashboardPortletManager, IPlacelessPortletManager)
  
  >>> sm.registerUtility(component=dashboardPortletManager,
  ...                    provided=IPortletManager,
  ...                    name='columns.dashboard')

  >>> dashboardFileName = os.path.join(tempDir, 'dashboard.pt')
  >>> open(dashboardFileName, 'w').write("""
  ... <html>
  ...   <body>
  ...     <div class="dashboard">
  ...       <tal:block replace="structure provider:columns.dashboard" />
  ...     </div>
  ...   </body>
  ... </html>
  ... """)
  
  >>> class DashboardPage(BrowserPage):
  ...     adapts(Interface, IBrowserRequest)
  ...     __call__ = ViewPageTemplateFile(dashboardFileName)
  >>> provideAdapter(DashboardPage, provides=IBrowserPage, name='dashboard.html')
  >>> view = getMultiAdapter((child1, TestRequest()), name='dashboard.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="dashboard">
      </div>
    </body>
  </html>
  
Let's register some portlets for the dashboard.

  >>> dashboard = getUtility(IPortletManager, name='columns.dashboard')
  
  >>> dashboard[USER_CATEGORY] = PortletCategoryMapping()
  >>> dashboard[USER_CATEGORY][Anonymous.id] = PortletAssignmentMapping()
  >>> dashboard[USER_CATEGORY][user1.id] = PortletAssignmentMapping()
  
  >>> dashboard[GROUP_CATEGORY] = PortletCategoryMapping()
  >>> dashboard[GROUP_CATEGORY][group1.id] = PortletAssignmentMapping()
  >>> dashboard[GROUP_CATEGORY][group2.id] = PortletAssignmentMapping()
  
  >>> saveAssignment(dashboard[USER_CATEGORY][user1.id], userPortlet)
  >>> saveAssignment(dashboard[GROUP_CATEGORY][group1.id], groupPortlet1)
  >>> saveAssignment(dashboard[GROUP_CATEGORY][group2.id], groupPortlet2)
  
When we render this, contextual portlets are ignored. Blacklistings also do
not apply.
  
  >>> dashboardAtChild1Manager = getMultiAdapter((child1, dashboard), ILocalPortletAssignmentManager)
  >>> dashboardAtChild1Manager.setBlacklistStatus(USER_CATEGORY, True)
  
  >>> dashboardAtChild1 = getMultiAdapter((child1, dashboard), IPortletAssignmentMapping)
  >>> saveAssignment(dashboardAtChild1, DummyPortlet('dummy for dashboard in context'))
  
  >>> view = getMultiAdapter((child1, TestRequest()), name='dashboard.html')
  >>> print view().strip()
  <html>
    <body>
      <div class="dashboard">
        <div>Dummy for user1</div>
        <div>Dummy for group1</div>
        <div>Dummy for group2</div>
      </div>
    </body>
  </html>
  
Portlet metadata
----------------

Sometimes, it is useful for a portlet renderer to know where the underlying
portlet came from, i.e. which manager, category, key and assignment name
were used to look it up. During the portlet retrieval process, that
information is made available as the ``__portlet_metadata__`` attribute on
the renderer.

  >>> class IDataAware(IPortletDataProvider):
  ...   pass
  
  >>> class DataAwarePortlet(Persistent, Contained):
  ...     implements(IPortletAssignment, IDataAware)
  ...     
  ...     def __init__(self, available=True):
  ...         self.available = available
  ...     data = property(lambda self: self)
  
  >>> class DataAwareRenderer(object):
  ...     implements(IPortletRenderer)
  ...     adapts(Interface, IBrowserRequest, IBrowserView, 
  ...             IPortletManager, IDataAware)
  ... 
  ...     def __init__(self, context, request, view, manager, data):
  ...         self.data = data
  ...         self.available = True
  ...
  ...     def update(self):
  ...         pass
  ...
  ...     def render(self, *args, **kwargs):
  ...         md = self.__portlet_metadata__
  ...         return "Manager: %s; Category: %s; Key: %s; Name: %s" % (md['manager'], md['category'], md['key'], md['name'],)

  >>> provideAdapter(DataAwareRenderer)
  
Let's assign this in the root folder.

  >>> dataPortlet = DataAwarePortlet()
  >>> leftAtRoot = getMultiAdapter((rootFolder, left), IPortletAssignmentMapping)
  >>> saveAssignment(leftAtRoot, dataPortlet)
  
Let's verify the output

  >>> view = getMultiAdapter((rootFolder, TestRequest()), name='main.html')
  >>> print view().strip()
  <html>
      <body>
        <div class="left-column">
          Manager: columns.left; Category: context; Key: ...; Name: DataAwarePortlet
          <div>Dummy for user1</div>
        </div>
        <div class="right-column">
          <div>Test document one</div>
          <div>Test document two</div>
        </div>
      </body>
    </html>
