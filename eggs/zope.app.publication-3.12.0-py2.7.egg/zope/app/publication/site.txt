======================
Using the site manager
======================

This test ensures that the site is correctly set and cleared in a thread
during traversal using event subscribers. Before we start, no site is set:

  >>> from zope.component import hooks
  >>> hooks.getSite() is None
  True

  >>> request = object()

  >>> from zope.app.publication import interfaces
  >>> from zope import site

On the other hand, if a site is traversed,

  >>> from zope.site.tests.test_site import SiteManagerStub, CustomFolder
  >>> sm = SiteManagerStub()
  >>> mysite = CustomFolder('mysite')
  >>> mysite.setSiteManager(sm)

  >>> from zope.traversing.interfaces import BeforeTraverseEvent
  >>> ev = BeforeTraverseEvent(mysite, request)
  >>> site.threadSiteSubscriber(mysite, ev)

  >>> hooks.getSite()
  <CustomFolder mysite>

Once the request is completed,

  >>> from zope.publisher.interfaces import EndRequestEvent
  >>> ev = EndRequestEvent(mysite, request)
  >>> site.clearThreadSiteSubscriber(ev)

the site assignment is cleared again:

  >>> hooks.getSite() is None
  True
