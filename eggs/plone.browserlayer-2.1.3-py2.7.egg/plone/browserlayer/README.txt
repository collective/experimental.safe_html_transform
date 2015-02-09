plone.browserlayer tests
------------------------

In testing.zcml we have registered a view, layer-test-view, available only for
the layer plone.browserlayer.tests.interfaces.IMyProductLayer.

Before the product is installed, we cannot view this:

    >>> from plone.browserlayer.tests.interfaces import IMyProductLayer
    >>> from plone.browserlayer import utils
    >>> IMyProductLayer in utils.registered_layers()
    False

    >>> from Products.Five.testbrowser import Browser
    >>> browser = Browser()
    >>> browser.open(self.portal.absolute_url() + '/@@layer-test-view')
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 404: Not Found
    
We can view a view registered for the default layer, though:

    >>> browser.open(self.portal.absolute_url() + '/@@standard-test-view')
    >>> print browser.contents
    A standard view
    
However, if we install the product the interface is registered in the local
site manager. Here we use the utility method directly, though we could also
use GenericSetup.
    
    >>> utils.register_layer(IMyProductLayer, name='my.product')
    >>> IMyProductLayer in utils.registered_layers()
    True
    
And if we now traverse over the site root and render the view, it should be
there.

    >>> browser.open(self.portal.absolute_url() + '/@@layer-test-view')
    >>> print browser.contents
    A local view
    
Unlike when applying a new skin, layers installed in this way do not override
views registered for the default layer.

    >>> browser.open(self.portal.absolute_url() + '/@@standard-test-view')
    >>> print browser.contents
    A standard view
    
It is also possible to uninstall a layer:

    >>> IMyProductLayer in utils.registered_layers()
    True
    >>> utils.unregister_layer(name='my.product')
    >>> IMyProductLayer in utils.registered_layers()
    False
    
    >>> browser.open(self.portal.absolute_url() + '/@@layer-test-view')
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 404: Not Found
    
GenericSetup support
--------------------

Most of the time, you will be registering layers using GenericSetup. Here
is how that looks.

    >>> from Products.CMFCore.utils import getToolByName
    >>> portal_setup = getToolByName(self.portal, 'portal_setup')

We should be able to install our product's profile. For the purposes of
this test, the profile is defined in tests/profiles/testing and 
registered in testing.zcml. It has a file called browserlayer.xml which
contains::

    <layers>
        <layer name="plone.browserlayer.tests" 
               interface="plone.browserlayer.tests.interfaces.IMyProductLayer" />
    </layers>

Let's import it:

    >>> IMyProductLayer in utils.registered_layers()
    False
    >>> _ = portal_setup.runAllImportStepsFromProfile('profile-plone.browserlayer:testing')
    >>> IMyProductLayer in utils.registered_layers()
    True

And just to prove that everything still works:

    >>> browser.open(self.portal.absolute_url() + '/@@layer-test-view')
    >>> print browser.contents
    A local view

    >>> browser.open(self.portal.absolute_url() + '/@@standard-test-view')
    >>> print browser.contents
    A standard view

We now also have uninstall support.  For the purposes of
this test, the profile is defined in tests/profiles/uninstall and 
registered in testing.zcml. It has a file called browserlayer.xml which
contains::

    <layers>
      <layer name="plone.browserlayer.tests"
             remove="true" />
    </layers>

Note that the contents of the 'remove' option do not actually matter; as long
as the option is not empty, we regard it as a request to remove the
layer.  This is how most GenericSetup importers treat the 'remove' option.

Also note that you do not need to specify the interface (though you
are allowed to); the name is enough.

Anyway, let's import it:

    >>> IMyProductLayer in utils.registered_layers()
    True
    >>> _ = portal_setup.runAllImportStepsFromProfile('profile-plone.browserlayer:uninstall')
    >>> IMyProductLayer in utils.registered_layers()
    False

And just to prove that everything still works (or fails to be found)
as expected:

    >>> browser.open(self.portal.absolute_url() + '/@@layer-test-view')
    Traceback (most recent call last):
    ...
    HTTPError: HTTP Error 404: Not Found

    >>> browser.open(self.portal.absolute_url() + '/@@standard-test-view')
    >>> print browser.contents
    A standard view
